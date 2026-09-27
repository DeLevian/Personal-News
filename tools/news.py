#!/usr/bin/env python3
"""Validate source/data contracts and rebuild deterministic indexes. No network/Git writes."""
from __future__ import annotations
import argparse, json, sys
from datetime import timedelta
from pathlib import Path
from contracts import ROOT, Invalid, require, load, day, timestamp, url, text, ID, DAY, section, counts, settings, make_schema, validate_edition, validate_catalogue

def edition_key(d): return d.get('edition_id',d['date'])
def edition_path(d): return f"data/{'initial' if d.get('edition_id') else 'daily'}/{d['date']}.json"
def editions(root=ROOT):
    cats={c['id'] for c in load(root/'docs/data/categories.json')['categories']}
    loaded=[(p,load(p)) for folder in ('daily','initial') for p in (root/f'docs/data/{folder}').glob('*.json')]
    loaded.sort(key=lambda p:timestamp(p[1]['generated_at']))
    result=[];ids=set();keys=set();events={}
    for path,d in loaded:
        validate_edition(d,cats,root)
        require(path.stem==d['date'] and path.relative_to(root/'docs').as_posix()==edition_path(d),'edition path mismatch')
        require(edition_key(d) not in keys,'duplicate edition key');keys.add(edition_key(d))
        for i in d['items']:
            require(i['id'] not in ids,'duplicate article ID');ids.add(i['id'])
            prior=events.get(i['event_id'])
            if i['status']=='NEW': require(prior is None,'known event cannot be NEW (including Radar and initial archive)')
            else:
                require(prior is not None,'UPDATE without prior event')
                require(i['previous']=={'id':prior['id'],'date':prior['date']},'UPDATE must refer to last version of same event')
                require(i['summary'].strip()!=prior['summary'].strip(),'UPDATE without changed summary')
            events[i['event_id']]={**i,'date':d['date']}
        result.append(d)
    return result

def derived(root,days):
    cfg=settings(root);ordered=list(reversed(days));newest=ordered[0]['date'] if days else None
    manifest={'version':2,'latest':edition_key(ordered[0]) if days else None,'updated_at':max((d['generated_at'] for d in days),key=timestamp) if days else None,'editions':[]}
    search={'version':2,'items':[]};events={}
    for d in ordered:
        manifest['editions'].append({'id':edition_key(d),'date':d['date'],'generated_at':d['generated_at'],'title':d['title'],'kind':d['kind'],'count':len(d['items']),'counts':counts(d['items']),'categories':sorted({i['category'] for i in d['items']}),'path':edition_path(d)})
        for i in d['items']:
            search['items'].append({'id':i['id'],'event_id':i['event_id'],'edition':edition_key(d),'category':i['category'],'section':section(i),'status':i['status'],'title':i['title'],'search_text':' '.join([i['title'],i['summary'],i['why_you_care'],*i['tags'],*(s['name'] for s in i['sources'])])})
    for d in days:
        for i in d['items']:
            events[i['event_id']]={'event_id':i['event_id'],'first_seen':events.get(i['event_id'],{}).get('first_seen',d['date']),'last_seen':d['date'],'last_item_id':i['id'],'last_edition':edition_key(d),'section':section(i),'title':i['title'],'last_summary':i['summary'],'sources':[s['url'] for s in i['sources']]}
    cutoff=day(newest)-timedelta(days=cfg['state_retention_days']-1) if days else day('1970-01-01')
    seen=sorted([v for v in events.values() if day(v['last_seen'])>=cutoff],key=lambda x:(x['last_seen'],x['event_id']),reverse=True)[:cfg['state_max_events']]
    ledger={'version':2,'events':{k:{'id':v['last_item_id'],'edition':v['last_edition']} for k,v in sorted(events.items())}}
    return {'docs/data/index.json':manifest,'docs/data/search.json':search,'state/seen.json':{'version':2,'as_of':newest,'retention_days':cfg['state_retention_days'],'max_events':cfg['state_max_events'],'events':seen},'state/event-index.json':ledger,'config/edition.schema.json':make_schema(cfg,load(root/'config/edition-v1.schema.json'))}

def write_json(path,data):
    path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');tmp.replace(path)
def run(root,command):
    validate_catalogue(root);days=editions(root)
    for path,data in derived(root,days).items():
        if command=='rebuild':write_json(root/path,data)
        else:require((root/path).exists() and load(root/path)==data,f'{path} not synchronized: run rebuild')
    print(f'OK: {len(days)} editions, {sum(len(d["items"]) for d in days)} items; catalogue, schema and indexes coherent.')
    return 0

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['validate','rebuild']);p.add_argument('--root',type=Path,default=ROOT);a=p.parse_args()
    try:return run(a.root,a.command)
    except (ValueError,TypeError,KeyError,OSError) as e:print('ERROR:',e,file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
