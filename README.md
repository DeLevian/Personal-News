# personal news. v2

**Sito:** https://delevian.github.io/Personal-News/

Una rassegna personale in italiano: News principali, Radar, eventuali scadenze del giorno, archivio e fonti. HTML/CSS/JavaScript statici; nessun framework, servizio AI o token nel browser.

## Cosa cambia
- News: obiettivo 10–16 elementi verificati; 24 ore normalmente, recupero motivato fino a 72.
- Radar: 0–8 segnalazioni più brevi, fino a 7 giorni. Accuratezza identica, peso editoriale differente.
- Fino a 3 “Da non perdere”, soltanto nelle News. “Da sapere oggi” solo per eventi/scadenze documentati, nascosto dopo la scadenza nella home e chiaramente storico nell'archivio.
- Ricerca e filtri Tutto/News/Radar, categorie, letti e salvati. Contatori coerenti: News+Radar = NEW+UPDATE.
- Feed, Radar, evidenze e risultati d'archivio ordinati per l'uscita reale della fonte: timestamp `published_at` quando verificabile, sola data come fallback senza inventare l'ora.
- Stesso design, modalità scura/chiara, vista compatta, navigazione mobile, URL permanenti e immagini ingrandibili.

Le quantità sono obiettivi, non quote da riempire. La discovery cerca 30–50 candidati per aumentare il bacino; un candidato non è ancora una notizia verificata.

## Leggere la notizia in italiano
La freccia a destra della stella apre un lettore interno a schermo intero, con sezioni, fonti, immagini e comandi per letti, salvati e condivisione. Il link “Leggi la fonte” continua ad aprire la fonte esterna. Back/Esc e “Notizie” chiudono il lettore; i link condivisi usano `?date=<edizione>&article=<ID>`. I vecchi link con `#ID` restano validi.

I testi sono articoli originali in italiano redatti dopo verifica, non traduzioni integrali di articoli protetti. Si trovano in `docs/data/articles/` e vengono cercati anche dalla ricerca del sito. Nessun modello o traduttore viene eseguito nel browser.

Le nuove News e i nuovi Radar richiedono un corpo italiano valido prima della pubblicazione. Gli item storici identici possono mostrare un avviso esplicito di sola sintesi finché non vengono integrati. Regole comuni a automazione e skill: `config/ARTICLE_CONTENT.md`. Parametri soltanto in `config/pipeline.json`, schema generato `config/article.schema.json`.

## Fonti canoniche
| Componente | Responsabilità |
|---|---|
| Second Brain privato / NEWS_PROFILE.md | Interessi e criteri personali |
| `config/SOURCES.json` | Dove cercare: fonti, tier, policy, query |
| `config/pipeline.json` | Limiti e finestre temporali |
| `config/DAILY_RUN.md` | Procedura completa della run |
| `config/ARTICLE_CONTENT.md` | Corpo originale italiano, citazioni e migrazione |
| `docs/data/articles/` | Testi completi separati dalle edizioni |
| `config/BRIEFING.md` | Messaggio finale breve |
| `docs/data/categories.json` | Presentazione delle sei categorie |
| `docs/data/daily/` e `initial/` | Archivio definitivo |
| `state/seen.json` e `event-index.json` | Cache recente e indice permanente |

Non copiare il profilo privato nel repository pubblico. Non mantenere una seconda lista di siti dentro categories.json o nel prompt del task.

## Discovery utilizzabile
`SOURCES.json` contiene 56 fonti nelle sei categorie, con ruoli primary/discovery/scouting e politiche daily/rotating/on_gap/optional. La rotazione è deterministica e non richiede un registro crescente da leggere ogni mattina.

```sh
python -m pip install -r requirements.txt
python tools/discovery.py plan --date YYYY-MM-DD
python tools/collect.py --date YYYY-MM-DD --output artifacts/discovery.json
python tools/discovery.py lookup --event-id ID
python tools/discovery.py audit --input artifacts/editorial-audit.json --output state/discovery-latest.json
```

Il planner non effettua ricerche. Il collector recupera metadati da indici pubblici con limiti di tempo/dimensione/concorrenza. L'agente deve poi integrare la ricerca web, raggruppare eventi, aprire le fonti e verificare date/fatti/rilevanza. Non esiste un provider AI nascosto nello script.
Il rapporto di copertura distingue successo, errore, blocco e nessun risultato. Un sito bloccato non è prova di assenza di notizie. Il mancato target richiede una spiegazione fattuale.

Prova iniziale: 50 link candidati da 30 controlli, di cui 27 recuperati via HTTP. Verifica separata di tutti i 56 indirizzi: 48 HTTP 200, 8 con blocco 403 del runner ma verificati via web. Non sono 50 notizie approvate. Evidenza: workflow Bootstrap v2 branch, run 36325422199.

## Dati e compatibilità
Lo schema v1 è congelato. Lo schema corrente accetta v1 e v2 ed è generato dai parametri di pipeline.json, evitando limiti diversi nel codice e nella documentazione.
`included_at` non è la data della fonte: conserva l'ammissione originaria negli aggiornamenti della stessa giornata. Non spostarla per far passare notizie vecchie e non usarla per l'ordinamento. `published_at`, quando presente, è l'istante reale verificato sulla fonte e viene mostrato in Europe/Rome; se la fonte pubblica soltanto il giorno, il sito mostra la data senza fabbricare un orario.
La migrazione del 27 settembre preserva gli otto articoli già pubblicati e l'archivio initial. `config/LEGACY_V1.json` conserva hash dei payload e ammissione originale solo per la medesima edizione: nessuna esenzione generica per vecchie news.
Ogni nuovo giorno parte direttamente da v2. Un evento visto in Radar resta noto quando esce dalla cache o cambia sezione. Un UPDATE richiede un delta reale e un riferimento all'ultimo precedente.

```sh
python tools/news.py rebuild
python tools/news.py validate
python -m unittest discover -s tests -v
node --check docs/assets/app.js
node --check docs/assets/reader.js
python tools/briefing.py
```

Il rebuild non riscrive le edizioni né redige testi: rigenera manifest, ricerca nel corpo, indice articoli, cache, ledger e schemi. `content_revision` segnala anche una modifica ai soli corpi senza alterare generated_at. `python tools/articles.py describe --item-id ID` prepara fingerprint e riferimenti per redigere il corpo. Un rerun senza novità non svuota l'edizione né crea falsi aggiornamenti.

## Test e sito locale

```sh
python -m http.server 8000 --bind 127.0.0.1 --directory docs
# Aprire http://localhost:8000
python -m pip install -r requirements-test.txt
python -m playwright install chromium
python tests/browser_check.py
python tests/browser_v2.py
python tests/browser_reader.py
python tests/live_check.py
```

Le fixture sintetiche sono solo in copie temporanee. I test verificano limiti, finestre, deduplicazione cross-section, schema fonti, vecchi link, ricerca, preferenze, immagini, scadenze e cinque larghezze. `dom_check.py` resta un alias di compatibilità al nuovo test HTTP.
La CI strutturale è indipendente dalla salute dei siti esterni. Il job live sul branch main attende il deploy, confronta dati/codice/CSS/HTML e verifica le immagini configurate. Source-health è una diagnostica manuale separata. Gli artifact contengono risultati e screenshot, non credenziali o dati privati.

## Uso quotidiano e privacy
Ultime news è sempre raggiungibile; precedente/successiva e archivio preservano date e link. Letti e salvati vivono nel browser: import/export permette il trasferimento, non c'è sincronizzazione cloud.
Il sito pubblico entra dalla root e rimanda a docs/. Non serve cambiare Pages. Le immagini rimangono sui server delle fonti, con credito, proporzioni corrette e fallback: la loro disponibilità futura non è garantita.

La pianificazione delle 07:00 Europe/Rome è un task ChatGPT esterno. Il suo prompt richiama soltanto AGENTS.md, DAILY_RUN.md e pipeline.json. Codice, Pages e un test manuale non dimostrano da soli la riuscita di una futura run programmata.
Vedere `project/STATE.md` per gli esiti reali della consegna.
