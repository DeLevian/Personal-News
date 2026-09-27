# Articoli italiani — contratto editoriale e tecnico

Questo è il contratto comune a run giornaliera, ricerca mirata e integrazione dello storico. Non copiare queste regole in altri repository: collegare questo file.

## Due livelli, una notizia

L'item nell'edizione mantiene titolo, sintesi breve, fonti, date, NEW/UPDATE e identità. La freccia a destra dei preferiti apre una lettura interna a schermo intero. Il link “Leggi la fonte” continua ad aprire il sito esterno. Condivisione, letti e salvati sono disponibili nel lettore e usano le preferenze esistenti.

Ogni nuovo item deve avere un corpo italiano completo in `docs/data/articles/<item_id>.json`, nello stesso commit dell'edizione e dei derivati. Non pubblicare prima la scheda e promettere il testo per dopo. Il browser legge JSON statici: non contiene un traduttore, un modello AI o credenziali.

## Scrittura: spiegare la notizia, non allungare la descrizione

Dopo verifica e deduplicazione, aprire le fonti e redigere un articolo autonomo e originale in italiano. Deve spiegare cosa è successo, i dettagli sostanziali, a chi si applica, disponibilità/prerequisiti e limiti realmente documentati. Contestualizzare l'impatto senza trasformare deduzioni in fatti. Un lettore deve poter capire la notizia senza dover aprire la pagina inglese.

Usare sezioni e paragrafi proporzionati alla materia. Non ripetere il sommario, non produrre riempitivi per raggiungere una lunghezza, non inventare esempi, specifiche o disponibilità mancanti. Conservare nomi di prodotti, versioni e termini tecnici quando tradurli li renderebbe ambigui. “Originale” non significa inventato: ogni affermazione fattuale deve essere supportata dalle fonti citate nella sua sezione.

La richiesta di lettura in italiano **non** autorizza a riprodurre o tradurre integralmente articoli protetti. Sintetizzare e riorganizzare i fatti con formulazioni e struttura proprie; eventuali citazioni devono essere brevi e attribuite. Non aggirare paywall o blocchi; non redistribuire gli articoli sorgente. La UI dichiara che si tratta di una redazione originale e mantiene i riferimenti agli originali.

Le soglie strutturali sono soltanto un controllo contro testi vuoti: i numeri sono in `pipeline.json > article_content`. Superare lo schema non dimostra accuratezza, buona qualità o lingua corretta; verificarle editorialmente prima della pubblicazione.

## Formato del corpo

`config/article.schema.json` è generato da `tools/articles.py` con i parametri della pipeline. Campi:

- `version: 1`, `item_id`, `language: "it"`, `editorial_mode: "original"`;
- `source_item_hash`: fingerprint del contenuto fattuale dell'item, calcolata da `tools.articles.item_hash`; non indovinarla;
- `verified_at` e `written_at`: verifica delle fonti del corpo e redazione, con offset; verifica non successiva alla redazione;
- `sources`: oggetti `name`, `type`, `url` HTTPS, senza credenziali, almeno una fonte già collegata all'item;
- `sections`: oggetti `heading`, `paragraphs` (array di stringhe di testo semplice), `source_urls` (URL presenti in `sources`). Ogni sezione cita le proprie fonti.

Non inserire HTML, widget, embed, script o testo Markdown da interpretare. Il lettore rende i contenuti con `textContent`. I timestamp del corpo non sostituiscono `published_at` o `included_at`: un approfondimento non ridata la notizia.

Per ottenere i riferimenti esatti prima di scrivere: `python tools/articles.py describe --item-id <ID>`. Il comando legge l'item e stampa percorso, fingerprint e fonti; non genera contenuti.

## Validazione e derivati

`python tools/news.py rebuild` controlla i corpi e genera anche `config/article.schema.json`, `docs/data/article-index.json` e la ricerca nel testo completo. `python tools/news.py validate` rifiuta nuovi item senza corpo, corpi orfani, identità errate, fingerprint obsolete, fonti/citazioni non valide e testi strutturalmente incompleti.

`docs/data/index.json > content_revision` cambia anche quando si modifica soltanto un approfondimento, senza cambiare le date originali dell'edizione. Il lettore carica il testo su richiesta; il feed resta leggero. Le liste restano ordinate per pubblicazione reale, non per data di redazione o commit.

Per un UPDATE servono sempre i fatti nuovi e il precedente secondo DAILY_RUN. Aggiornare il corpo insieme all'item se cambiano i fatti, altrimenti la fingerprint blocca la pubblicazione. Un miglioramento della sola prosa non è un UPDATE editoriale e non crea un nuovo evento.

## Storico e migrazione

Gli item v1/v2, gli ID, i permalink e `config/LEGACY_V1.json` non sono riscritti per introdurre il lettore. Il manifesto congelato `config/ARTICLE_LEGACY.json` ammette **solo** gli identici item già esistenti alla migrazione senza corpo esteso; in quel caso il lettore mostra un avviso “scheda storica” e la sintesi, senza fingere un articolo completo.

Non rigenerare o estendere il manifesto nelle run ordinarie. Un nuovo ID, anche con data retrodatata, non eredita l'eccezione. I nuovi item richiedono sempre il corpo, inclusi Radar e UPDATE.

Per integrare lo storico, rileggere le fonti e aggiungere il corpo separato con l'ID esistente, senza nuovi NEW/UPDATE, senza cambiare included_at, senza ritoccare le ricevute. Se una fonte non è verificabile, mantenere il fallback dichiarato e segnalare la lacuna. Gli errori HTTP del corpo sono invece segnalati come errore di caricamento con pulsante Riprova, non come assenza definitiva dell'articolo.

## Controlli prima della consegna

Oltre ai controlli canonici: `node --check docs/assets/reader.js` e `python tests/browser_reader.py`. Verificare apertura dalla freccia, link esterni, chiusura/Back/Esc, ritorno ai filtri e alla posizione, permalink/reload, letti/salvati/condivisione, ricerca nel corpo, temi, immagini/fallback, errori e retry, sicurezza del testo, mobile e assenza di overflow. Le fixture restano soltanto in copie temporanee.

Dopo il deploy, controllare che HTML, JavaScript, CSS, indici e corpi serviti corrispondano al commit, quindi aprire realmente un articolo sul sito. Distinguere test locale/CI, commit, deploy e verifica live. La chat resta un briefing breve: l'articolo si legge sul sito.
