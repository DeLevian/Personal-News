# personal news.

Una rassegna personale, non un'altra pagina di rumore. Ultima edizione in apertura, archivio navigabile, fonti e immagini, ricerca trasversale, letti e salvati.

**Repository:** `DeLevian/Personal-News` · **Lingua:** italiano · **Stack:** HTML / CSS / JavaScript + JSON. Nessun framework, nessuna API key nel browser, nessuna build necessaria.

## Aprire il sito
Dalla cartella clonata:

```sh
python -m http.server 8000 --bind 127.0.0.1 --directory docs
```

Aprire `http://localhost:8000`. Su Windows è utilizzabile anche `py -m http.server 8000 --bind 127.0.0.1 --directory docs`.

Il doppio clic sul file HTML non basta: i browser limitano fetch dei JSON da `file://`. Il file root `index.html` è solo un ingresso che rimanda a `docs/` preservando query e collegamento all'articolo. La pagina canonica è `docs/index.html`.

## Cosa c'è
- La home apre sempre l'ultima edizione disponibile; le date esplicite negli URL aprono lo storico.
- “Ultime news” resta visibile anche mentre si legge un'edizione precedente.
- Frecce precedente/successiva, archivio con filtro per mese, cronologia indietro/avanti del browser.
- Notizie in evidenza, sei categorie esplorabili, ricerca nell'edizione o in tutto lo storico.
- Card con banner/miniature della fonte, credito, fallback e immagini disattivabili.
- NEW/UPDATE, data della fonte separata dalla data della newsletter, delta e collegamento precedente.
- Salvati e letti nel browser, vista compatta, tema automatico/chiaro/scuro.
- Esporta/importa preferenze per trasferire letture e salvati tra dispositivi (non sincronizzazione cloud).
- Link permanenti alle notizie. Scorciatoie tastiera, finestre accessibili, reduced motion, stampa.
- Avviso quando l'ultima edizione disponibile è vecchia. Verifica dell'indice al ritorno sulla pagina e ogni 5 minuti mentre è aperta.

La prima edizione è un **bootstrap retrospettivo del 27 settembre 2026**: sei articoli reali pubblicati fra il 16 e il 22 settembre, con fonti consultate durante l'allestimento. Non finge una rassegna delle ultime 24 ore. Non sono state create edizioni pregresse artificiali. Con una sola edizione le frecce sono correttamente disabilitate.

## Struttura

```text
AGENTS.md                    contratto per gli agenti
index.html                   ingresso verso docs/
docs/index.html              template stabile
docs/assets/                 CSS, JavaScript, favicon
docs/data/categories.json    mappa UI e argomenti da esplorare
docs/data/daily/              un JSON per edizione
docs/data/index.json          navigazione cronologica, generata
docs/data/search.json         ricerca nello storico, generata
state/seen.json               cache eventi recente, generata
config/pipeline.json          riferimenti, limiti, stato pubblicazione
config/DAILY_RUN.md           procedura per la newsletter
config/edition.schema.json   contratto dati
tools/news.py                validazione e ricostruzione indici
tools/image_metadata.py      estrazione offline metadati immagini
tests/                       test riproducibili
project/STATE.md             stato verificato e limiti
```

## Aggiungere un'edizione
Seguire `AGENTS.md` e `config/DAILY_RUN.md`. Modificare solo il nuovo JSON quotidiano, poi:

```sh
python tools/news.py rebuild
python tools/news.py validate
python -m unittest discover -s tests
node --check docs/assets/app.js
```

I comandi Python usano solo la libreria standard (Python 3.10+). Il validatore verifica struttura e coerenza dei riferimenti; non può stabilire da solo la verità delle notizie. Indice, ricerca e stato sono derivati: niente duplicazione manuale quotidiana. I cambiamenti vanno committati insieme.

L'indice di ricerca completo cresce con l'archivio, ma viene caricato dal sito solo quando necessario. L'agente ordinario usa la cache compatta; consulta lo storico soltanto per confronti mirati. Un'eventuale suddivisione mensile dell'indice è un'evoluzione, non un requisito attuale.

## Profilo editoriale
La fonte personale canonica resta in `DeLevian/Second-Brain`, file `03_PROJECTS/Second-Brain-News/NEWS_PROFILE.md`.
Il sito non scarica il Second Brain né contiene credenziali. Le categorie sono una mappa derivata, non una copia indipendente delle preferenze.

## Immagini e privacy
Le immagini restano sui server delle fonti. Non sono incorporate copie degli articoli o immagini scaricate senza permesso. URL e provenienza sono indicati nei JSON. La raggiungibilità dei file binari non è stata confermata dall'ambiente di sviluppo: il fallback è intenzionale ed è testato. I titolari possono bloccare hotlink o rimuovere contenuti. I riquadri di categoria non sono fotografie sostitutive.
Le richieste delle immagini arrivano ai relativi server; si possono disattivare dalle preferenze. Nessun tracker, font remoto o script esterno. Letture e salvati non lasciano il browser salvo esportazione esplicita.

## Pubblicazione: non ancora attivata
Il repository rimane **privato**. Aggiungere file non pubblica automaticamente un sito né attiva la newsletter.

**Attenzione:** GitHub Pages normalmente espone il sito sul web anche quando il repository è privato. Per repository privati la disponibilità dipende dal piano GitHub. Non rendere pubblico il repository come scorciatoia.

Fonti ufficiali:
- https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site
- https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages

Soltanto dopo una decisione esplicita sulla visibilità: pubblicare esclusivamente `docs/` su hosting appropriato; per mantenerlo privato serve controllo di accesso lato hosting, non una password JavaScript. Non esporre config/, state/, dati riservati o il Second Brain. `robots.txt` e `noindex` non sono una protezione di accesso.

## Automazione
`config/DAILY_RUN.md` è pronta per un agente con web e accesso GitHub. Non c'è un cron autonomo né una promessa di esecuzione futura: occorre collegare e verificare la pianificazione esterna. Questo caricamento non riattiva l'automazione precedentemente sospesa.

## Verifiche browser opzionali
Con Playwright installato:

```sh
python tests/browser_check.py
python tests/dom_check.py
```

`browser_check.py` usa un server HTTP locale e copie temporanee per la navigazione tra due edizioni. `dom_check.py` verifica DOM e layout senza rete con sostituti in memoria per fetch, storage e history. È un test di componenti, non equivalente all'end-to-end HTTP. Per un Chromium di sistema impostare `CHROMIUM_PATH`.

Gli esiti effettivamente ottenuti e le verifiche ancora aperte sono in `project/STATE.md`.
