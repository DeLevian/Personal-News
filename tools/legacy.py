"""Frozen v1 inclusion receipts, only for the same already-published edition.
A receipt never makes an old event new or allows it into a future day's edition.
"""
import copy,hashlib,json
from pathlib import Path

def payload_hash(item):
    payload={k:v for k,v in item.items() if k not in ('section','included_at')}
    return hashlib.sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()

def admitted(item,edition,root):
    path=Path(root)/'config/LEGACY_V1.json'
    if not path.exists():return False
    record=json.loads(path.read_text()).get('items',{}).get(item['id'])
    return bool(record and record['edition']==edition['date'] and not edition.get('edition_id') and item.get('section')=='main' and item.get('included_at')==record['included_at'] and payload_hash(item)==record['payload_sha256'])

def promote(d,root):
    if d['version']==2:return copy.deepcopy(d)
    if d['kind']!='daily':raise ValueError('The initial archive must not be promoted.')
    data=copy.deepcopy(d);data['version']=2
    records=json.loads((Path(root)/'config/LEGACY_V1.json').read_text())['items']
    for item in data['items']:
        record=records.get(item['id'])
        if not record or record['edition']!=data['date'] or record['payload_sha256']!=payload_hash(item):raise ValueError('No exact frozen v1 receipt for this article; do not fabricate one during an ordinary run.')
        item['section']='main';item['included_at']=record['included_at']
    return data
