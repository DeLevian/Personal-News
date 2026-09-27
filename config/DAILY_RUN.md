# Procedura editoriale giornaliera

## Obiettivo
Aggiornare `DeLevian/Personal-News` con un'edizione in italiano, normalmente 5-12 notizie realmente utili (anche zero, senza riempitivi). Il sito legge i dati: NON riscrivere HTML, CSS o JavaScript ogni giorno.

## Letture minime
1. `AGENTS.md` di questo repository, questa procedura e `config/pipeline.json`.
2. In `DeLevian/Second-Brain`: `AGENTS.md`, `INDEX.md`, poi soltanto il `profile_path` indicato nella configurazione. Gli indici servono per il routing, non autorizzano una scansione.
3. `docs/data/categories.json`, `state/seen.json`, `docs/data/index.json`.
4. Leggere una vecchia edizione solo per un confronto mirato. Per un possibile evento più vecchio della cache, cercare l'event_id nell'indice di ricerca/archivio prima di classificarlo NEW.

## Ricerca
Usare data/ora effettive in Europe/Rome. Finestra ordinaria 24 ore; recupero eccezionale fino a 72 ore con `recency_reason`. Confrontare data dell'evento e data dell'articolo: un pezzo ripubblicato non rende nuovo l'evento.
Usare le categorie come query iniziali e il profilo come criterio editoriale. Le fonti configurate sono punti di partenza, non una whitelist.
Aprire le fonti primarie e riportare URL reali. Non trasformare snippet, rumor o benchmark del produttore in fatti indipendentemente verificati. Niente articoli inventati, date fittizie, immagini non pertinenti o edizioni pregresse simulate.
Non copiare interi articoli. Scrivere sintesi originali brevi e una ragione di interesse; non includere dettagli personali sensibili o dati aziendali.

## Immagini
Cercare og:image/twitter:image nell'HTML dell'articolo, oppure un'immagine ufficiale effettivamente associata alla notizia. `tools/image_metadata.py` può estrarre l'URL da HTML già recuperato.
Registrare URL HTTPS, alt, credito e source_url. Verificare accessibilità quando possibile e registrare i limiti nel campo `verification`.
Le preview non dimostrano una licenza di ripubblicazione: non scaricare né redistribuire immagini protette senza permesso. Mantenerne il collegamento alla fonte, rispettare restrizioni e termini. Se nessuna immagine adatta è disponibile, `image: null`.
Non salvare redirect temporanei con token, URL di tracking o endpoint privati. Il frontend ha un fallback e un comando per disattivare le immagini.

## Preparazione e deduplicazione
Un'edizione ha `version`, `date`, `generated_at` con offset locale, `kind: daily`, `title`, `summary`, `items` ed eventuale `note`.
Consultare `config/edition.schema.json` per il contratto completo. Ogni articolo ha id univoco prefissato dalla data ed event_id stabile.
- NEW: non già segnalato nell'archivio.
- UPDATE: evento già presente, ma sviluppo nuovo sostanziale. Aggiungere `delta` e `previous: {id,date}` dell'ultima scheda del medesimo evento.
- Già noto senza novità: omettere.
Massimo 3 `featured`. Non forzare tutte le categorie a comparire in ogni edizione.
Una data fonte ignota non equivale a oggi: escludere dalla rassegna corrente o trattarla come approfondimento retrospettivo esplicito. `kind: bootstrap` è riservato all'avvio iniziale, non un modo di aggirare la freschezza quotidiana.

## Persistenza
1. Rileggere HEAD. Se l'edizione di oggi esiste già, non sostituirla alla cieca; rendere la ripetizione idempotente. Correggere solo con motivo esplicito, preservando gli articoli validi e gli ID.
2. Scrivere `docs/data/daily/YYYY-MM-DD.json`.
3. Eseguire `python tools/news.py rebuild`: ricostruisce indice cronologico, ricerca globale e cache eventi (30 giorni, massimo 200).
4. Eseguire `python tools/news.py validate` e i test. La validazione è strutturale: NON sostituisce la verifica editoriale delle fonti.
5. Commit atomico di edizione + `docs/data/index.json` + `docs/data/search.json` + `state/seen.json`. Non toccare il template. In caso di conflitto di HEAD, riconciliare senza force.
6. Rileggere i file/commit dal repository. Non dichiarare riuscita una scrittura solo tentata.

Se l'agente dispone solo dei connettori, può ottenere i file necessari e validare nel proprio ambiente; costruire poi tree/commit/ref mediante GitHub. Se non può verificare dati o scrivere, segnalare il blocco e NON inventare successo. L'HTML nella chat non è un sostituto della persistenza richiesta.

## Notifica
Al massimo 2-3 righe: data, numero notizie, numero in evidenza, link al sito solo se `website_url` è configurato e realmente verificato. Altrimenti link all'edizione/commit su GitHub, dichiarando che il sito non è pubblicato.
Non inviare tutto il testo della newsletter in chat.

## Pianificazione
Questi file non avviano automaticamente alcun job. La pianificazione delle 07:00 è esterna e deve essere verificata/attivata separatamente con gli strumenti disponibili e l'autorizzazione dell'utente.

## Sito pubblico e archivio iniziale (2026-09-27)
L’utente ha autorizzato e attivato Pages; `website_url` contiene il link effettivo. Riutilizzarlo nella notifica. La selezione iniziale del mattino è stata preservata in `docs/data/initial/2026-09-27.json` (edition_id distinto, stessa data reale). Non modificarla nelle run ordinarie. Il rebuild include sia daily sia initial.
Non assumere che un og:image sia corretto: controllare protocollo, contenuto e caricamento. Le immagini generiche/loghi sono indicate come tali, non fotografie della notizia. I test live fanno fallire la verifica se una preview configurata non si carica.
