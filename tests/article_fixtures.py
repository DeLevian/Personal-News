"""Synthetic editorial bodies: temporary test repositories only."""
import copy
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from articles import item_hash
from contracts import ROOT
import news


def article(item):
    urls = [s['url'] for s in item['sources']]
    return {'version': 1, 'item_id': item['id'], 'language': 'it', 'editorial_mode': 'original',
            'source_item_hash': item_hash(item), 'written_at': item['verified_at'],
            'verified_at': item['verified_at'], 'sources': copy.deepcopy(item['sources']),
            'sections': [
                {'heading': 'Che cosa verifica questa prova', 'source_urls': urls,
                 'paragraphs': [
                     'Questa è una notizia sintetica creata esclusivamente per verificare il lettore. Non descrive prodotti reali e non deve essere pubblicata sul sito. La parola archiviolettoreunico permette di controllare che anche il corpo esteso sia incluso nella ricerca, senza dipendere dal titolo o dalla breve descrizione della scheda.',
                     'Il primo blocco controlla paragrafi, titoli e collegamenti alle fonti. La lunghezza serve soltanto a esercitare il contratto software in una copia temporanea del progetto. Nessun contenuto di questa prova deve diventare una notizia della rassegna personale.']},
                {'heading': 'Limiti della simulazione', 'source_urls': urls,
                 'paragraphs': [
                     'Il secondo blocco verifica la navigazione e la corretta distinzione tra fonti esterne e pagina interna. Leggere questo testo non dimostra che una fonte pubblica sia stata controllata. I test devono mantenere separati gli esempi artificiali dagli articoli reali, ripristinare lo stato locale e lasciare invariati i file delle edizioni pubblicate.']}
            ]}


def write_articles(root, edition):
    root = Path(root)
    if root.resolve() == ROOT.resolve():
        raise ValueError('Synthetic articles may not be written into the production repository')
    for item in edition['items']:
        news.write_json(root / f'docs/data/articles/{item["id"]}.json', article(item))
