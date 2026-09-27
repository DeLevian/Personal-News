"""Final one-time migration. Changes stay on the reviewed branch until tests pass."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from news import load,write_json
from legacy import payload_hash,promote

def replace(path,old,new):
 p=ROOT/path;s=p.read_text()
 if new in s:return
 if old not in s:raise RuntimeError('Missing anchor '+path+' '+old[:80])
 p.write_text(s.replace(old,new))

cfg=load(ROOT/'config/pipeline.json');cfg['category_candidate_targets']={'p1':[5,8],'p2':[4,6]};write_json(ROOT/'config/pipeline.json',cfg)
replace('tools/discovery.py',"'candidate_target':[5,8] if category in {'ai','agents','work','gamedev'} else [4,6]", "'candidate_target':cfg['category_candidate_targets']['p1' if category in {'ai','agents','work','gamedev'} else 'p2']")
replace('tools/contracts.py',"    require(cfg['timezone']=='Europe/Rome'", "    require(set(cfg.get('category_candidate_targets',{}))=={'p1','p2'} and all(isinstance(v,list) and len(v)==2 and all(type(n) is int for n in v) and 0<v[0]<=v[1] for v in cfg['category_candidate_targets'].values()),'invalid category candidate targets')\n    require(cfg['timezone']=='Europe/Rome'")
replace('tools/contracts.py',"        if i.get('published_at'):\n            pub=timestamp(i['published_at']);require(pub.date()==day(i['published_date']),'source timestamp/date mismatch')\n        else:","        from legacy import admitted\n        if admitted(i,d,root):continue  # Exact, same-edition v1 inclusion; no re-dating.\n        if i.get('published_at'):\n            pub=timestamp(i['published_at']);require(pub.date()==day(i['published_date']),'source timestamp/date mismatch')\n        else:")
cat=load(ROOT/'config/SOURCES.json')
for s in cat['sources']:
 if s['id']=='blender':s.update(enabled=True,verification_method='http_content',notes='HTTP 200 e titolo Blender Release Notes verificati su GitHub Actions il 2026-09-27; il browser di ricerca era bloccato.')
 if s['id'] in ['openai','chatgpt-notes','localllama','dolphin','dokkan-community','terramaster','androidauthority','deck-community']:
  s['access_hint']='Esistenza/contenuto verificati via web; HTTP automatizzato 403 nel controllo del 2026-09-27. Usare ricerca web e fonti alternative, non concludere assenza di news.'
write_json(ROOT/'config/SOURCES.json',cat)
p=ROOT/'docs/assets/v2.css'
if '.lead h3{overflow-wrap:anywhere}' not in p.read_text():p.write_text(p.read_text()+'\n.lead h3{overflow-wrap:anywhere}\n')
# Eliminate tests whose outcome depended on tomorrow's date or cache retention.
replace('tests/test_pipeline.py',"self.base.pop('edition_id',None)","self.base.pop('edition_id',None)\n        self.next_date=(news.day(self.days[-1]['date'])+timedelta(days=1)).isoformat()")
replace('tests/test_pipeline.py',"d['date']='2026-09-28';d['generated_at']='2026-09-28T07:00:00+02:00'", "d['date']=self.next_date;d['generated_at']=self.next_date+'T07:00:00+02:00'")
replace('tests/test_pipeline.py',".replace('2026-09-27','2026-09-28')", ".replace(self.base['date'],self.next_date)")
replace('tests/test_pipeline.py',"self.root/'docs/data/daily/2026-09-28.json'", "self.root/f'docs/data/daily/{self.next_date}.json'")
replace('tests/test_pipeline.py',"self.assertEqual(m['latest'],'2026-09-28')", "self.assertEqual(m['latest'],self.next_date)")
replace('tests/test_pipeline.py',"seen=news.load(self.root/'state/seen.json')\n        self.assertTrue(any(e['event_id']=='pi-v0-87-1' for e in seen['events']))", "seen=news.load(self.root/'state/event-index.json')\n        self.assertIn('pi-v0-87-1',seen['events'])")
# Stronger Pages verification: HTML/CSS as well as script and data.
replace('tests/live_check.py',"if edition_bytes_match:\n                        base=candidate;ready=True;break", "asset_bytes_match=all(hashlib.sha256(read(candidate+name+'?check='+str(time.time_ns()))).digest()==hashlib.sha256((ROOT/'docs'/name).read_bytes()).digest() for name in ['index.html','assets/v2.css'])\n                    if edition_bytes_match and asset_bytes_match:\n                        base=candidate;ready=True;break")
replace('tests/live_check.py',"        page.locator('#mobile-archive').click();", "        counts=latest.get('counts',{'main':latest['count'],'radar':0})\n        page.locator('[data-section-filter=radar]').click();expect(page.locator('.card')).to_have_count(counts['radar'])\n        page.locator('[data-section-filter=main]').click();expect(page.locator('.card')).to_have_count(counts['main'])\n        page.locator('[data-section-filter=all]').click();expect(page.locator('.card')).to_have_count(latest['count'])\n        report['section_filters']='passed';report['counts']=counts\n        page.locator('#mobile-archive').click();")
# Freeze evidence for unchanged existing daily entries; do not rewrite initial archive.
path=ROOT/'docs/data/daily/2026-09-27.json';d=load(path)
receipt=ROOT/'config/LEGACY_V1.json'
if not receipt.exists():
 assert d['version']==1
 write_json(receipt,{'version':1,'source_commit':'c5f4c6d581ec16157aa1ec2b0605c4e8f41c1135','note':'Frozen same-edition v1 admission receipt. included_at uses the last known v1 edition timestamp, not an invented source publication hour. Never regenerate during daily runs.','items':{i['id']:{'edition':d['date'],'included_at':d['generated_at'],'payload_sha256':payload_hash(i)} for i in d['items']}})
if d['version']==1:
 d=promote(d,ROOT);now=datetime.now(ZoneInfo('Europe/Rome')).isoformat(timespec='seconds');assert now.startswith('2026-09-27')
 rows=[('openai-gpt6-prompt-caching-2026-09-22','ai','2026-09-22','OpenAI: strumenti per capire quando la cache dei prompt funziona','OpenAI ha presentato una dashboard e strumenti diagnostici per osservare il riuso dei prompt e individuare i cache miss. La documentazione illustra anche come mantenere stabili istruzioni e definizioni degli strumenti.','Un approfondimento utile per integrare agenti via API: non implica automaticamente una riduzione delle quote del proprio abbonamento ChatGPT.','OpenAI','https://openai.com/index/better-prompt-caching-for-gpt-6/'),('terramaster-tos-7-0-1278','devices','2026-09-24','TerraMaster TOS 7.0.1278: correzioni per memoria e gestione dei file','L’annuncio dello staff elenca correzioni al consumo di memoria del centro messaggi, alla copia delle cartelle e ad alcuni accessi SMB. L’aggiornamento x86 richiede TOS 7.0.0746 o successivo; il produttore raccomanda un backup prima di procedere.','Da valutare sul proprio modello e sulla versione installata, non come invito a un aggiornamento automatico o applicabile a ogni NAS.','TerraMaster · annuncio dello staff','https://forum.terra-master.com/en/viewtopic.php?t=10622')]
 for eid,category,pub,title,summary,why,name,source in rows:
  assert not any(i['event_id']==eid for folder in ['daily','initial'] for f in (ROOT/f'docs/data/{folder}').glob('*.json') for i in load(f)['items'])
  item={'id':'2026-09-27-'+eid,'event_id':eid,'section':'radar','category':category,'status':'NEW','title':title,'summary':summary,'why_you_care':why,'published_date':pub,'event_date':pub,'verified_at':'2026-09-27T16:25:12+02:00','included_at':now,'featured':False,'tags':['Radar','API' if category=='ai' else 'NAS'],'sources':[{'name':name,'type':'official','url':source}],'image':None}
  if category=='ai':
   icon=next(i['image'] for i in d['items'] if i['event_id']=='chatgpt-security-history-2026-09-25')
   item['image']=dict(icon)
  d['items'].append(item)
 d['generated_at']=now;d['note']='Edizione aggiornata al formato v2: otto notizie già pubblicate preservate e due segnalazioni Radar verificate. La raccolta di 50 link candidati è una prova di discovery, non 50 notizie approvate.'
 deadline=next(i for i in d['items'] if i['event_id']=='champions-global-challenge-2027-i-battles')
 d['attention_today']={'text':'Champions: per chi è già iscritto, la fase di lotta della Global Challenge termina il 28 settembre alle 03:59 italiane.','item_ids':[deadline['id']],'source_url':deadline['sources'][0]['url'],'valid_from':now,'expires_at':'2026-09-28T03:59:00+02:00'}
 write_json(path,d)
print('Final migration applied without re-dating existing articles.')
