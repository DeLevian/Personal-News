# Personal News — stato di consegna

Aggiornato: 2026-09-27.

## Implementato
- Applicazione statica in italiano: home sull'ultima edizione, archivio, categorie, ricerca per edizione e globale.
- Card con immagini esterne, fallback, fonti, date distinte, NEW/UPDATE, motivazione personale.
- Letti/salvati nel browser, import/export, tema, vista compatta, navigazione mobile e link permanenti.
- Unica edizione reale: 2026-09-27, bootstrap retrospettivo di 6 articoli pubblicati dal 16 al 22 settembre; non rassegna delle ultime 24 ore.
- JSON Schema, validatore, generazione deterministica di indice/ricerca/cache eventi, procedura giornaliera.
- Profilo personale canonico esterno nel Second Brain. Nessuna copia del Second Brain nel sito.

## Verifiche eseguite
- `python tools/news.py validate`: PASS.
- `python -m unittest discover -s tests -v`: 15 test PASS.
- `node --check docs/assets/app.js`: PASS.
- `tests/dom_check.py` con Chromium: PASS. Rendering, filtri, ricerca globale, letti/salvati, dialoghi, temi, fallback immagini e navigazione mobile verificati con fetch/storage/history in memoria.
- Nessun overflow orizzontale a 320, 390, 768, 1024 e 1440 px. Screenshot desktop e mobile ispezionati.

## Limiti di verifica
Il test HTTP completo `tests/browser_check.py` è stato tentato ma la policy del browser dell'ambiente blocca tutte le navigazioni URL (`ERR_BLOCKED_BY_ADMINISTRATOR`). Non sono state cambiate le policy. La verifica DOM non certifica cronologia browser reale, persistenza dopo reload, clipboard/download o funzionamento sull'hosting finale.
Le tre immagini configurate provengono dai collegamenti degli articoli Unity. La raggiungibilità HTTP dei file immagine non è stata confermata; nessuna immagine protetta è stata copiata. Gli altri tre articoli non hanno immagini configurate.
La validazione dei dati non sostituisce il controllo editoriale delle fonti.

## Pubblicazione e automazione
- Repository privato. Hosting non configurato e pubblicazione pubblica non autorizzata.
- Nessun nuovo cron, workflow pianificato o automazione attivato dal progetto.
- Le 07:00 Europe/Rome sono l'orario previsto, non una prova di pianificazione attiva.
- Questo progetto non riattiva l'automazione ChatGPT esistente.

## Prossimi passi
Decidere hosting e controllo di accesso; eseguire il test HTTP sul browser reale; collegare la pianificazione esterna e verificare una run end-to-end con persistenza.
