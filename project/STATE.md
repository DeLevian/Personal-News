# Personal News v2 — stato tecnico

Aggiornato: 2026-09-27.

## Implementazione
Profilo nel Second Brain privato; SOURCES.json per fonti/query; pipeline.json per limiti; DAILY_RUN.md/BRIEFING.md per processo e notifica; categories.json soltanto UI.

Target: 10–16 News, 0–8 Radar, 3 featured solo News. Main 24 ore, eccezione 72 con motivo; Radar 7 giorni. Discovery 30–50 candidati e copertura di tutte le sei categorie. Nessun minimo di pubblicazione imposto.

56 fonti: 41 primarie, 11 discovery, 4 community. Controlli quotidiani mirati e rotazione deterministica, senza rileggere l'intero Second Brain.

## Compatibilità e dati
Lo schema v1 è conservato e il frontend legge v1/v2. News/Radar condividono NEW/UPDATE, ricerca, archivio, preferenze e indice permanente degli eventi oltre alla cache recente.
L'edizione del 27 settembre contiene otto News preesistenti, conservate con gli stessi payload/ID, e due nuovi Radar verificati. L'archivio iniziale non è stato riscritto. Le ricevute hash LEGACY_V1 valgono soltanto per gli item identici nella stessa edizione, non per pubblicare vecchie notizie in altri giorni.
Attenzione opzionale con scadenza, avviso storico distinto da quello corrente; immagini ingrandibili, proporzioni preservate, fallback; nessun dato sintetico nei JSON pubblicati.

## Verifiche concluse sul branch
- Primo bootstrap: run 36325422199, 62 test Python e browser HTTP superati.
- Finalizzazione: run 36326127301, tentativo 2, 66 test Python e due suite browser HTTP superati; commit generato 891b0a26102766abf276e1684cb9474418ca38c7.
- Coperti contratti, limiti, finestre, attenzione, deduplicazione cross-section, sicurezza URL/testo, ricevute v1, vecchi link, ricerca, saved/read, temi, lightbox e cinque larghezze.
- Primo controllo delle 56 fonti: 48 recuperi HTTP riusciti, 8 blocchi 403 del runner con contenuto verificato via web. Un blocco non viene equiparato ad assenza di notizie.
- Prova collector: 50 link candidati da 30 controlli, 27 recuperati. Sono metadati reali da verificare, non 50 eventi approvati né una rassegna giornalistica completa.

## CI e pubblicazione
Rimossi il workflow temporaneo con permessi di scrittura e gli script di migrazione. La CI permanente è in sola lettura: contratto/dati e browser separati dalla verifica Pages; salute fonti su diagnostica manuale separata.
Sito pubblico autorizzato: https://delevian.github.io/Personal-News/ . L'ingresso root rimanda a docs/; hosting e visibilità invariati.
Il workflow Verify Personal News su main confronta contenuti distribuiti e verifica realmente immagini, layout e navigazione. L'esito del job published-site e gli artifact live-browser-evidence attestano il deploy specifico, non il semplice successo del commit.

## Automazione
La run delle 07:00 Europe/Rome è gestita dal task ChatGPT Personal News. Deve richiamare AGENTS.md, DAILY_RUN.md e pipeline.json tramite il bootstrap breve, senza una copia delle regole nel task. Per stato enabled, fuso e prompt effettivi fare riferimento allo strumento automazioni; il repository non crea un secondo cron.

## Limiti
Quantità editoriali non garantite; fonti e immagini esterne possono cambiare disponibilità. Ricerca aperta e verifica umana/agentica delle fonti rimangono necessarie: il collector non è un redattore autonomo. Letti/salvati sono locali, con import/export. I test Chromium non certificano tutti i browser/dispositivi.
