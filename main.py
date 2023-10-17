import requests
from bs4 import BeautifulSoup
import csv
import re
import time

print('\n[ AS24 SCRAPER 1.0.1 by rickorso ]')
print('Inizializzazione...')
time.sleep(1.0)

# Crea una funzione per aggiungere il parametro &page=1 dopo &desc=numero
def add_page_param(url):
    # Cerca il parametro &desc=numero nell'URL
    match = re.search(r'&desc=\d+', url)
    
    if match:
        # Estrai la parte dell'URL prima del parametro &desc=numero
        prefix = url.split(match.group())[0]
        
        # Aggiungi il parametro &page=1
        return f"{prefix}&page=1{match.group()}"
    else:
        # Se il parametro &desc=numero non è presente, restituisci l'URL originale
        return url

# Crea una funzione per sostituire i dati mancanti e quelli con "-"
def replace_missing(data):
    return ["N/A" if "-" in item else item for item in data]

# Sostituisci "Elettrica/xxx" con "Ibrida"
def replace_hybrid(data):
    return ["Ibrida" if "Elettrica/Benzina" in item or "Elettrica/Diesel" in item else item for item in data]

# Richiedi all'utente di inserire l'URL della prima pagina di ricerca su AutoScout24
base_url = input("\nInserisci l'URL della pagina desiderata su AutoScout24: ")

# Aggiungi il parametro &page=1 se necessario
base_url = add_page_param(base_url)

# Definisci un'espressione regolare per cercare il parametro &page= con un numero qualsiasi
pattern = r'&page=\d+'

# Estrai il valore corrente del parametro &page=
match = re.search(pattern, base_url)

if match:
        current_page = match.group()
        page_number = int(current_page.split('=')[1])  # Estrai il numero dalla stringa
        if page_number > 1:     # Se la pagina rilevata è maggiore di 1, essa viene riportata a 1 in modo da ricominciare da capo
            page_number = 1
        url = re.sub(pattern, f'&page={page_number}', base_url)  # Sostituisci il numero di pagina

# Crea una lista per salvare tutti gli annunci da tutte le pagine
annunci_totali = []

# Effettua la richiesta GET
response = requests.get(url)

# Parsa il contenuto HTML della pagina
soup = BeautifulSoup(response.content, 'html.parser')

page_counter = int(soup.find('div', class_='ListPage_pagination__v_4ci').find_all('button', class_='FilteredListPagination_button__41hHM')[-2].get_text())

""" print('Page counter: ', page_counter) """

for page_number in range(1, page_counter+1):

    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Definisci un'espressione regolare per cercare il parametro &page= con un numero qualsiasi
    pattern = r'&page=\d+'
    
    # Estrai il valore corrente del parametro &page=
    match = re.search(pattern, url)

    if match:
        current_page = match.group()
        
        if page_number > 1:
            print(f'Pagina ({page_number})')
        else:
            print('\nAcquisizione link...\n')
            time.sleep(0.5)
            print('Link acquisito correttamente.\n')
            print('Inizio acquisizione dati...\n')
            time.sleep(0.5)
            print(f'Pagina ({page_number})')

    # Verifica che la richiesta abbia avuto successo
    if response.status_code == 200:

        # Estrai i dati desiderati dagli annunci
        annunci = []

        print('Acquisizione dati in corso...\n')

        for annuncio in soup.find_all('article', class_='cldt-summary-full-item listing-impressions-tracking list-page-item false ListItem_article__ppamD'):
            link = annuncio.find('a', class_='ListItem_title__znV2I ListItem_title_new_design__lYiAv Link_link__pjU1l').get('href')
            link = 'https://www.autoscout24.it' + link
            vers = annuncio.find('a', class_='ListItem_title__znV2I ListItem_title_new_design__lYiAv Link_link__pjU1l').find('h2')
            vers = vers.find('span', class_='ListItem_version__jNjur')
            vers = vers.text.strip()
            auto = annuncio.find('a', class_='ListItem_title__znV2I ListItem_title_new_design__lYiAv Link_link__pjU1l').find('h2')
            auto.find('span', class_='ListItem_version__jNjur').decompose()
            auto = auto.text.strip()

            # Cerca il prezzo in due modi differenti
            prezzo = annuncio.find('p', class_='Price_price__WZayw PriceAndSeals_current_price__XscDn')
            if prezzo:
                prezzo = prezzo.text.strip()
            else:
                prezzo = annuncio.find('span', class_='SuperDeal_highlightContainer__EPrZr')
                if prezzo:
                    prezzo = prezzo.text.strip()
                else:
                    prezzo = "N/A"

            # Estrai tutti i div con la classe specificata
            dettagli = annuncio.find_all('span', class_='VehicleDetailTable_item__koEV4')

            # Ottieni il testo da ciascun div e uniscilo con delle virgole
            dettagli_formattati = ';'.join([d.text.strip() for d in dettagli])

            # Divide i dettagli in una lista separata
            dettagli_separati = dettagli_formattati.split(';')

            # Sostituisci i dati mancanti e quelli con "-" con "N/A"
            dettagli_separati = replace_missing(dettagli_separati)

            # Sostituisci "Elettrica/xxx" con "Ibrida"
            dettagli_separati = replace_hybrid(dettagli_separati)

            # Aggiungi tutte le colonne
            annunci.append([auto, vers, prezzo] + dettagli_separati + [link])

        # Aggiungi gli annunci estratti dalla pagina corrente alla lista totale
        annunci_totali.extend(annunci)

        url = re.sub(pattern, f'&page={page_number + 1}', url)  # Sostituisci il numero di pagina
        
        if page_number == page_counter:
            print('Acquisizione terminata. Finalizzazione...')

    else:
        print('La richiesta non ha avuto successo. Codice di stato:', response.status_code)
        break

filename = input("\nInserisci un nome per il file in cui verranno estratti i dati acquisiti: ")
filename = filename + '.csv'

# Esporta i dati in un file CSV
while True:

    try:
        with open(filename, 'w', newline='') as file_csv:
            print(f'\nScrittura in corso su file "{filename}"...')
            writer = csv.writer(file_csv, delimiter=';')
            writer.writerow(['Auto', 'Versione', 'Prezzo', 'Chilometraggio', 'Cambio', 'Anno di immatricolazione', 'Alimentazione', 'Potenza', 'Link'])
            writer.writerows(annunci_totali)
        print(f'\nDati estratti ed esportati con successo in "{filename}".')
        break  # Esci dal ciclo se la scrittura ha successo
    except PermissionError:
        print("PermissionError: Impossibile scrivere sul file selezionato. Verifica che il file selezionato non sia attualmente aperto sul Desktop.")
        retry = input("\nVuoi ritentare la scrittura? (S/N): ")
        if retry.lower() != 's':
            break  # Esci dal ciclo se l'utente non vuole ritentare
    except Exception as e:
        print(f'Errore sconosciuto: {e}')
