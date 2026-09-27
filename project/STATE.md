# Personal News — stato operativo

Aggiornato: 2026-09-27.

## Stato corrente
L’utente ha reso pubblico il repository e attivato Pages. Il link è https://delevian.github.io/Personal-News/ e viene usato nelle notifiche tramite config/pipeline.json.

Prova manuale del flusso quotidiano: sei notizie verificate del 25–27 settembre, tre in evidenza. Due entro 24 ore, quattro recuperi motivati entro 72 ore. Nessun vecchio annuncio viene ripubblicato come nuovo.

La selezione iniziale del mattino (sei articoli del 16–22 settembre) è conservata separatamente con stessa data reale e ID `2026-09-27-initial`. Indici, ricerca, deduplicazione e vecchi link la includono. Le run ordinarie non la modificano.

## Immagini
Tutte le schede delle due edizioni hanno un URL di immagine proveniente dalla fonte. Screenshot/banner autentici quando disponibili; il logo OpenAI è esplicitamente dichiarato come logo della fonte. Credito/provenienza, proporzioni preservate, ingrandimento e fallback in caso di errori. Nessuna copia locale di immagini protette.

## Verifica
- Validatore/rebuild e 18 test Python: superati localmente.
- Controllo sintattico JavaScript e test DOM responsive: superati localmente.
- Il browser locale della sandbox blocca le navigazioni HTTP: per i test end-to-end è stato aggiunto un workflow GitHub Actions in sola lettura, senza modificare la pianificazione delle news.
- Prima esecuzione CI: individuato un errore nel selettore CSS del test dei link (ID iniziavano con cifre), corretto usando selettori per attributo.
- Le prove HTTP/browser e le immagini effettive sono registrate dal workflow **Verify Personal News**; consultare l’esito del commit corrente e gli artifact `browser-evidence`, non presumere il successo da questa descrizione.

## Confini
Le immagini esterne possono cambiare disponibilità. Non è promessa compatibilità universale con ogni browser/dispositivo. Letti e salvati sono locali, con esportazione/importazione, non sincronizzazione cloud.
