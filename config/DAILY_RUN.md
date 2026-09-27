# Personal News v2 — run giornaliera canonica

## Scopo e fonti di verità
Completare ricerca ampia, verifica, selezione News/Radar, persistenza, controlli e briefing. Non fermarsi a un elenco di link né a una ricerca generica. Non modificare il template ogni mattina.
- Profilo personale: il percorso profile_path in DeLevian/Second-Brain.
- Fonti e query tecniche: config/SOURCES.json.
- Parametri numerici: config/pipeline.json. Non mantenere copie dei limiti nel task.
- Schema effettivo: config/edition.schema.json, generato dai parametri; il contratto v1 resta congelato per lo storico.
- UI: docs/data/categories.json, senza topics o discovery_sources duplicati.

## 1. Lettura mirata e preflight
Leggere AGENTS.md, questa procedura e pipeline.json. Nel Second Brain leggere prima AGENTS.md e INDEX.md, poi solo NEWS_PROFILE.md per il contenuto personale. Nessuna scansione generale, nessuna copia del profilo nel repository pubblico.
Leggere indice, seen.json e source map. Consultare vecchi JSON o state/event-index.json soltanto per confronti mirati; l'assenza dalla cache non prova che un evento sia nuovo.
Controllare strumenti effettivi: web, lettura/scrittura GitHub, ambiente Python. Usare i connettori disponibili; non chiedere attività manuali evitabili. Se mancano capacità, non fingere ricerca, scrittura o test e non iniziare una pubblicazione parziale.
Rilevare data/ora effettive Europe/Rome e HEAD di main. Se oggi esiste un'edizione, preservarne articoli validi, ID e orari di inclusione. Installare requirements.txt per i comandi Python; il sito resta statico.

## 2. Discovery ampia, prima della selezione
Usare discovery_candidate_target_min/max: inizialmente 30–50 eventi candidati unici, non una quota da inventare. Esplorare tutte e sei le categorie, non soltanto quelle con più risultati.
`python tools/discovery.py plan --date YYYY-MM-DD` prepara fonti giornaliere, rotazione e query. Il piano non è una ricerca effettuata.
`python tools/collect.py --date YYYY-MM-DD --output artifacts/discovery.json`, quando disponibile, raccoglie titoli e link reali da indici selezionati. Sono metadati non verificati: possono essere vecchi o irrilevanti. Non pubblicarli automaticamente.
Ordine di lavoro:
1. Fonti daily e quota rotating proposta dal piano, privilegiando i produttori dei tool seguiti.
2. Tier 2 specialistiche per ampliare candidati e coprire sottodomini mancanti.
3. Ricerca web aperta guidata da query_matrix. Spezzare query troppo ampie per prodotto/sottodominio; cercare anche in inglese. La lista non è una whitelist.
4. Tier 3 solo per scouting/testimonianze; ricondurre i fatti verificabili alle fonti primarie.
Non servono tutte le fonti ogni giorno. La rotazione è deterministica per data; non richiede un grosso stato per-fonte. I report di salute possono restare negli artifact, distinti dalla memoria editoriale.

### Copertura minima
- AI: OpenAI/ChatGPT/API/Codex, Anthropic, modelli locali, Ollama, Qwen e modelli emergenti pertinenti.
- Agenti: Pi/estensioni, MCP, terminale/IDE, coding agent, integrazioni.
- Lavoro: Copilot Studio, M365 Copilot, SharePoint, Teams, Entra, RAG/enterprise search, KB e documenti.
- GameDev: Unity/Web/mobile, authoring/Odin, asset AI 2D/3D, rigging/animazione, Blender/Krita/GIMP, workflow modulari.
- Gaming: separatamente Champions, Dokkan, Pocket; poi generi, console/ecosistemi, retrogaming e macro-aree. Nessuna nuova watchlist permanente di singoli titoli; distinguere Global/JP, piattaforma e fuso.
- Dispositivi: Windows, NVIDIA, Android/Samsung, Steam Deck/SteamOS, Switch 2, Xbox, TerraMaster. Non duplicare Gaming.
I target per categoria sono in category_candidate_targets. Sotto target, ampliare query/fonti prima di concludere, senza inventare candidati.

### Traccia di copertura
Prima delle sintesi mantenere un audit di run: version:2, checked_at, checks, candidates.
Check: category, method source/web_search, source_id oppure query, outcome success/blocked/error/no_results, evidence breve e fattuale.
Candidato: event_id dopo raggruppamento, title, URL canonico, category, published_date se verificata, decision main/radar/known/outdated/irrelevant/unverified, reason breve.
`python tools/discovery.py audit --input artifacts/editorial-audit.json --output state/discovery-latest.json` verifica copertura/duplicati e produce un riepilogo compatto. Sotto il target serve shortfall_reason concreto. Un sito bloccato non significa nessuna notizia.
Registrare evidenze e decisioni editoriali, non ragionamenti interni o dati privati. Report completo come artifact; discovery-latest.json è solo l'ultimo riepilogo, non un log crescente.

## 3. Verifica e deduplicazione
Raggruppare fonti del medesimo evento prima di contarle. Togliere tracking dagli URL, ma non considerare una pagina release-notes condivisa come un singolo evento eterno.
Aprire gli articoli selezionabili. Verificare date, versione, piattaforma, preview/GA e disponibilità; un commento recente o una ripubblicazione non è un annuncio nuovo. Per ogni candidato selezionabile cercare anche il timestamp reale di pubblicazione (`published_at`) nella fonte, nei metadati `datePublished`, RSS/API o timestamp del post, preservando offset/fuso. Attribuire benchmark e dichiarazioni del fornitore.
Cercare l'event_id nella cache e, se necessario, nel ledger permanente con `python tools/discovery.py lookup --event-id ID`; aprire la scheda precedente per confrontare i fatti.
- NEW: evento mai fornito nell'intero archivio.
- UPDATE: sviluppo sostanziale, delta esplicito e previous dell'ultimo id/data del medesimo evento.
- Già noto: omettere. Radar→News senza fatti nuovi non è un aggiornamento.
Anche gli eventi initial restano nel ledger dopo l'espulsione da seen.json.

## 4. Selezione News e Radar
Applicare pipeline.json: inizialmente target 10–16 News, 0–8 Radar, massimo 3 featured solo News. Sono obiettivi e massimi, non minimi obbligatori di pubblicazione.
News: sviluppo significativo, 24 ore normalmente; massimo 72 con recency_reason.
Radar: segnalazione minore ma verificata, massimo 7 giorni; mai già fornita senza sviluppo sostanziale. Non significa minore accuratezza né raccolta di rumor.
Con poche notizie valide ampliare prima la discovery nei sottodomini scoperti; poi pubblicare meno, mai riempitivi o contenuti fuori finestra. Le immagini non sono requisito di ammissione.

## 5. Dati e tempo
Nuove edizioni version:2, kind:daily; item section:main|radar e included_at, oltre agli altri campi del contratto.
included_at è l'ora reale di prima inclusione, non la pubblicazione della fonte. Non cambiarla per far sembrare fresca una news o a ogni rerun. verified_at <= included_at <= generated_at.
`published_at` rappresenta esclusivamente l'istante reale di pubblicazione della fonte: non usare `included_at`, `verified_at`, `generated_at`, ora di crawl, ora del commit o un generico `updated_at` come sostituti. Recuperarlo ogni volta che la fonte espone un orario verificabile. Una fonte con sola data non autorizza un orario inventato: in quel caso lasciare `published_at` assente, conservare `published_date` e, se noto, `published_timezone` IANA. Il frontend ordina dal più recente al più vecchio usando `published_at`; per gli elementi senza ora usa la data e, nello stesso giorno, li colloca dopo quelli con timestamp preciso. Il validatore usa un limite conservativo; se la finestra Main non è dimostrabile, valutare Radar o escludere.
Le edizioni v1 restano leggibili come News. Per la sola migrazione sono state congelate ricevute con hash in config/LEGACY_V1.json: consentono di mantenere i contenuti identici nella stessa edizione, senza cambiarne pubblicazione o data. Non rigenerare ricevute né usarle per nuove giornate. `tools/legacy.py` espone promote per una conversione esatta, non un bypass di freschezza. L'edizione iniziale non va promossa/modificata nelle run ordinarie.

### Da sapere oggi
attention_today facoltativo: text, item_ids, source_url realmente presente negli item, valid_from ed expires_at con offset. Solo eventi/scadenze verificati, pertinenti al giorno e non terminati. La UI nasconde gli avvisi scaduti nella home e li etichetta come storici nell'archivio.

## 6. Immagini dopo la selezione
Preferire screenshot/banner specifico, poi og:image/social preview o immagine ufficiale pertinente. Logo solo ultima alternativa, dichiarato come logo; altrimenti image:null.
Registrare HTTPS, alt, credito, source_url e verifica effettiva. Nessun URL inventato, segreto o temporaneo con credenziali. image_metadata.py estrae metadati da HTML già recuperato.
Non aggirare accessi né redistribuire immagini protette senza autorizzazione. Verificare i file immagine, non soltanto uno status 200 che potrebbe essere HTML. Il sito gestisce proporzioni, lightbox e fallback.

## 7. Persistenza idempotente e controlli
Un rerun senza nuove notizie non deve svuotare/duplicare l'edizione né cambiare generated_at per produrre un commit. Il report di copertura può cambiare solo per verifiche realmente nuove. Una nuova giornata senza news può avere un'edizione vuota esplicita.
Scrivere l'edizione, `python tools/news.py rebuild`, `python tools/news.py validate`, `python -m unittest discover -s tests -v`.
Il rebuild genera manifest, ricerca, seen, ledger e schema; non riscrive le edizioni archiviate. Conservare entrambi i livelli editoriali in ricerca, link e preferenze.
Rileggere HEAD, preparare commit coerente di edizione+derivati+eventuale riepilogo discovery su main senza force. In caso di concorrenza riconciliare. Una validazione fallita blocca la pubblicazione.
Rileggere commit/file, verificare separatamente CI, deploy e contenuto servito. Per UI includere sintassi JS e browser. La salute esterna è diagnostica separata dalla CI strutturale.
Non dichiarare Pages verificato solo perché il commit è riuscito. Attendere i contenuti del commit corrente, compresi indici e immagini; in caso di timeout dichiarare deploy in attesa o limite osservato.

## 8. Briefing in chat
Usare config/BRIEFING.md e tools/briefing.py: circa 8–10 righe, data, conteggi coerenti, titoli featured, avviso valido, esiti reali e website_url.
NEW+UPDATE deve uguagliare News+Radar. Le aggiunte in questa run sono diverse dal totale dell'edizione: riportarle solo con confronto verificato. Due aggiunte a otto notizie non significa una newsletter di sole due news.
Nessun testo completo della newsletter, test inesistenti, successo presunto o modello dedotto dalla chat.

## Pianificazione
Task ChatGPT esterno con solo bootstrap verso questa procedura. Non creare copie, non modificare hosting/visibilità o il Second Brain durante una run normale. Mantiene 07:00 Europe/Rome e legge le versioni canoniche aggiornate.
