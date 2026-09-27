# Personal News v2 — stato operativo

Aggiornato: 2026-09-27.

## Consegna verificata
La v2 è stata unita su main tramite PR #1, merge `330217b5cec0b74492380467f6dff20b49629987`, dopo sviluppo sul branch `chatgpt/personal-news-v2` e verifica separata.
Il workflow **Verify Personal News**, run **36326833388**, ha concluso con successo sia `structure-and-browser` sia `published-site` sul commit distribuito. Il sito reale è https://delevian.github.io/Personal-News/ e l'ingresso rimanda a docs/ senza variazioni di hosting.

## Architettura e parametri
Profilo nel Second Brain privato; SOURCES.json per fonti/query; pipeline.json per limiti; DAILY_RUN.md/BRIEFING.md per processo e notifica; categories.json soltanto UI.
Target 10–16 News, 0–8 Radar, 3 featured solo Main. Main 24 ore, eccezione 72 con motivo; Radar 7 giorni. Discovery 30–50 candidati e copertura delle sei categorie, non quote di pubblicazione obbligatorie.
56 fonti: 41 primarie, 11 discovery, 4 community; controlli mirati e rotazione deterministica. Nessuna scansione quotidiana dell'intero Second Brain.

## Compatibilità e dati
Lo schema v1 è conservato e il frontend legge v1/v2. News/Radar condividono NEW/UPDATE, ricerca, archivio, preferenze e indice permanente degli eventi oltre alla cache recente.
L'edizione del 27 settembre contiene **8 News + 2 Radar**, 10 NEW e 0 UPDATE, 3 evidenze. Gli otto payload precedenti e gli ID sono preservati; l'archivio iniziale non è stato riscritto. Le ricevute hash LEGACY_V1 valgono solo per contenuti identici nella stessa edizione, non per ripubblicare vecchie notizie in altri giorni.
Avviso del giorno opzionale con scadenza; etichetta storica distinta; immagini con proporzioni preservate, ingrandimento e fallback. Nessuna fixture sintetica è entrata nei dati pubblicati.

## Verifiche effettive
- **66 test Python** superati, schema/catalogo/indici coerenti, controllo sintattico JavaScript superato.
- Due suite HTTP Chromium: filtri Main/Radar, ricerca globale, NEW/UPDATE cross-section, vecchi link, saved/read dopo reload, temi, attenzione corrente/scaduta/storica, lightbox, sicurezza testo e cinque larghezze.
- Pages reale: **14 immagini configurate su 14 caricate**, sezioni e contatori corretti, navigazione e lightbox superati, nessun errore JavaScript, nessun overflow a 320/390/768/1024/1440 px.
- Source-health iniziale: 56 fonti, 48 HTTP riusciti e 8 blocchi del runner con contenuto verificato via web. Il collector ha recuperato 50 link candidati da 30 controlli (27 riusciti): non sono 50 notizie approvate.
- Evidenza: https://github.com/DeLevian/Personal-News/actions/runs/36326833388 ; artifact `structural-browser-evidence` e `live-browser-evidence`. Il workflow del commit corrente resta il riferimento per eventuali verifiche successive.

## Automazione e sicurezza
Il task ChatGPT esistente **Personal News** è stato aggiornato il 2026-09-27 alle 16:44 Europe/Rome: **enabled**, cadenza giornaliera **07:00 Europe/Rome**, prompt breve che avvia AGENTS.md, DAILY_RUN.md e pipeline.json. Nessun nuovo task creato. Il modello non è esposto dai metadati e non viene dedotto.
Rimossi il workflow temporaneo con permessi di scrittura e gli script di migrazione. CI permanente in sola lettura; salute fonti in diagnostica manuale separata. Nessuna modifica a visibilità/hosting e nessuna credenziale o copia del Second Brain inserita nel repository pubblico.

## Limiti e osservazione
Le quantità sono target; fonti e immagini possono cambiare disponibilità. Un blocco va completato con ricerca aperta o dichiarato, non interpretato come assenza di notizie. Il collector non sostituisce verifica e selezione editoriale.
Letti/salvati sono locali con import/export, non sincronizzati. Test Chromium non equivalgono a certificazione di ogni dispositivo. Resta da osservare la prima run programmata della v2: test e deploy riusciti non garantiscono anticipatamente una futura esecuzione del servizio ChatGPT.
