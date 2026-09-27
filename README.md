# personal news.

**Sito:** https://delevian.github.io/Personal-News/

Rassegna personale in italiano: ultima edizione, archivio, categorie, ricerca, immagini ingrandibili, letti e salvati. HTML/CSS/JavaScript e JSON, senza framework, chiavi API nel browser o build obbligatoria.

## Uso
La home apre le news più recenti. Il pulsante Ultime news rimane visibile; le frecce e l’archivio permettono di tornare alle edizioni precedenti. Ricerca nell’edizione o in tutto lo storico, filtri, salvati/non letti, modalità compatta, tema automatico/chiaro/scuro. Le miniature rispettano le proporzioni originali e si possono ingrandire.

Letti, salvati e preferenze sono conservati nel browser, non sincronizzati automaticamente. Importa/esporta dalle preferenze per trasferirli tra dispositivi. I link permanenti aprono l’edizione e l’articolo corretti.

## Dati e aggiornamento
- `docs/index.html`, `docs/assets/`: template stabile, non rigenerato ogni mattina.
- `docs/data/categories.json`: mappa di visualizzazione/scoperta derivata dal profilo personale.
- `docs/data/daily/YYYY-MM-DD.json`: edizioni correnti.
- `docs/data/initial/2026-09-27.json`: selezione iniziale del mattino, con id `2026-09-27-initial`. Non è una giornata precedente inventata.
- `docs/data/index.json`, `search.json`, `state/seen.json`: file derivati automaticamente.
- `config/DAILY_RUN.md`: procedura editoriale canonica.
- `config/pipeline.json`: link sito, riferimenti e limiti.

Il profilo personale rimane nel Second Brain privato; non è copiato nel sito. La selezione del mattino e la prova giornaliera del 27 settembre sono entrambe navigabili con la loro data reale. Gli ID degli articoli e i vecchi link sono preservati.

```sh
python tools/news.py rebuild
python tools/news.py validate
python -m unittest discover -s tests -v
node --check docs/assets/app.js
```

Python 3.10+, libreria standard per dati e validazione. La validazione strutturale non sostituisce la verifica giornalistica. Non far passare come NEW un evento presente nell’archivio iniziale o in una vecchia edizione.

## Avvio locale

```sh
python -m http.server 8000 --bind 127.0.0.1 --directory docs
```

Aprire http://localhost:8000. Su Windows anche `py -m http.server 8000 --bind 127.0.0.1 --directory docs`. Il doppio clic su HTML non basta per fetch dei JSON. L’index nella root rimanda a docs/; Pages pubblica esclusivamente docs/.

## Verifica browser e immagini
`tests/browser_check.py` esegue test HTTP con Chromium: ricerca, letti/salvati e persistenza, navigazione reale, link vecchi, filtri, tema, mobile e cinque larghezze. Le immagini esterne sono deliberatamente bloccate in questo test per verificare il fallback.

`tests/live_check.py` controlla invece il sito Pages effettivo: attende i dati e il codice correnti, carica ogni immagine delle ultime due edizioni, verifica dimensioni naturali, lightbox, layout e navigazione. Non sostituisce i test di tutte le piattaforme possibili.

```sh
python -m pip install playwright pillow
python -m playwright install chromium
python tests/browser_check.py
python tests/live_check.py
```

In GitHub Actions, **Verify Personal News** esegue verifiche in sola lettura a ogni push. Screenshot e risultati JSON sono negli artifact `browser-evidence`. Non modifica i dati e non pianifica la newsletter. Un’immagine che viene bloccata/rimossa dal fornitore può fallire in futuro: il fallback resta sempre attivo.

## Privacy e pubblicazione
L’utente ha reso pubblico il repository e abilitato Pages il 2026-09-27. Il sito non contiene credenziali o copie del Second Brain. Anche config e state sono visibili nel repository pubblico, ma non sono la radice del sito.

Le immagini provengono dai siti delle fonti, con credito e collegamento. Nessuna copia di foto protette viene redistribuita dal repository. Dove manca un banner specifico, un logo ufficiale è esplicitamente identificato come logo, non come fotografia della novità. Disattivare le immagini nelle preferenze elimina le richieste ai rispettivi server durante la visualizzazione.

La newsletter delle 07:00 Europe/Rome è gestita dall’automazione ChatGPT esterna; questo repository non contiene un cron autonomo. Consultare `project/STATE.md` per lo stato di prova e i limiti verificati.
