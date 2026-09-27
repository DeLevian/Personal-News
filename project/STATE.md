# Personal News v2 — stato di implementazione

Aggiornato: 2026-09-27. Questo file descrive fatti di sviluppo; l'esito live è nei workflow del commit distribuito.

## Architettura
Profilo nel Second Brain privato; SOURCES.json per fonti/query; pipeline.json per limiti; DAILY_RUN.md/BRIEFING.md per processo e notifica; categories.json soltanto UI.
Schema v1 conservato e v2 News/Radar; indice permanente eventi oltre alla cache recente. Ricevute hash congelate per conservare l'ammissione degli otto item v1 nella medesima giornata, non per riutilizzarli come news future.

## Parametri
Target 10–16 News, 0–8 Radar, 3 featured solo News; 24 ore Main, massimo72 con motivo; Radar7giorni. Discovery30–50 candidati, copertura sei categorie; fonti56 (41 primarie,11 discovery,4 community). Rotazione deterministica, no scansione quotidiana dell'intero Second Brain.

## Implementazione verificata su branch
- 62 test Python e due suite HTTP Chromium superati nel primo bootstrap, run36325422199.
- Main/Radar, filtri, contatori, ricerca, Radar→Main dedup, attenzione valida/scaduta, vecchi URL, temi, lightbox, XSS text safety e cinque larghezze verificati.
- 56 fonti controllate:48 HTTP200,8 HTTP403 del runner ma contenuto/esistenza verificati via web. Blender, inizialmente bloccato via web, è HTTP200 sul runner ed è stato abilitato.
- Collector:50 link candidati reali da30 controlli (27 recuperati), non50 fatti verificati. Gli output restano artifact, non vengono spacciati per news selezionate.
- I test delle ricevute e i controlli finali vengono eseguiti nel workflow di finalizzazione; consultare l'esito reale del branch/commit.

## Dati
Archivio initial e ID preservati. L'edizione del27settembre viene convertita conservando gli otto payload originali e integrando due Radar reali (prompt caching OpenAI, aggiornamento TOS TerraMaster) e l'avviso Champions già documentato. Nessun articolo sintetico viene pubblicato.
I test generano esempi in copie temporanee e controllano che l'archivio reale non sia modificato.

## Pubblicazione / automazione
Sito autorizzato e già attivo: https://delevian.github.io/Personal-News/ . L'ingresso root rimanda a docs/, senza variazioni di hosting.
La promozione su main, la verifica live del commit finale e l'aggiornamento del task07:00 saranno registrati nelle verifiche di consegna, non presunti da questo stato intermedio.

## Limiti permanenti
Le fonti possono bloccare scraping; il flusso deve completare via web e dichiarare copertura incompleta. Immagini esterne possono diventare indisponibili. Letti/salvati sono locali con import/export. Il target quantitativo non garantisce un minimo quotidiano.
