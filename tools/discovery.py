#!/usr/bin/env python3
"""Plan broad editorial discovery, deduplicate candidates, audit coverage.
The plan is NOT a search result. The agent performs the searches and records evidence.
No provider keys or private profile are stored here.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from contracts import ROOT,CATEGORIES,ID,Invalid,require,load,day,timestamp,url,text,validate_catalogue
from news import write_json

def canonical_url(value):
    require(url(value),'candidate URL must be HTTPS')
    u=urlsplit(value)
    query=[(k,v) for k,v in parse_qsl(u.query,keep_blank_values=True) if not k.lower().startswith('utm_') and k.lower() not in {'fbclid','gclid','srsltid','sid'}]
    return urlunsplit((u.scheme,u.netloc.lower(),u.path or '/',urlencode(query),''))

def plan(root,when):
    cfg,cat=validate_catalogue(root);date_value=day(when);output={}
    for category in sorted(CATEGORIES):
        src=[s for s in cat['sources'] if s['enabled'] and s['category']==category]
        daily=[s for s in src if s['check_policy']=='daily']
        rotating=sorted([s for s in src if s['check_policy']=='rotating'],key=lambda s:s['id'])
        if rotating:
            offset=(date_value.toordinal()*cfg['rotating_per_category'])%len(rotating)
            rotating=(rotating[offset:]+rotating[:offset])[:cfg['rotating_per_category']]
        output[category]={'priority':1 if category in {'ai','agents','work','gamedev'} else 2,'candidate_target':[5,8] if category in {'ai','agents','work','gamedev'} else [4,6], 'check_first':daily+rotating,'on_gap':[s for s in src if s['check_policy']=='on_gap'],'optional':[s for s in src if s['check_policy']=='optional'],'open_web_queries':cat['query_matrix'][category]}
    return {'version':2,'date':when,'target_unique_candidates':[cfg['discovery_candidate_target_min'],cfg['discovery_candidate_target_max']],'coverage_required':sorted(CATEGORIES),'categories':output,'rule':'Inspect every category, expand gaps, then verify/select. Do not claim this plan is completed discovery. Dates/facts/URLs must be checked on the article. Rotation is deterministic and requires no per-source history scan.'}

def audit(root,data):
    cfg,cat=validate_catalogue(root);require(data.get('version')==2,'invalid discovery report')
    checked=timestamp(data['checked_at']);known={s['id'] for s in cat['sources']}
    checks=data.get('checks',[]);candidates=data.get('candidates',[])
    require(isinstance(checks,list) and isinstance(candidates,list),'invalid checks/candidates')
    coverage=set()
    for c in checks:
        require(c.get('category') in CATEGORIES and c.get('method') in ('source','web_search'),'invalid check')
        require(c.get('outcome') in ('success','blocked','error','no_results'),'invalid check outcome')
        if c['method']=='source':require(c.get('source_id') in known,'unknown source check')
        else:require(text(c.get('query'),500),'query required')
        require(text(c.get('evidence'),600),'check evidence required (not chain of thought)')
        coverage.add(c['category'])
    require(coverage==CATEGORIES,'every category must have an attempted check; blocked is not no news')
    urls=set();events=set();summary={c:0 for c in sorted(CATEGORIES)}
    for i in candidates:
        require(i.get('category') in CATEGORIES and text(i.get('title'),220),'invalid candidate')
        require(isinstance(i.get('event_id'),str) and ID.fullmatch(i['event_id']),'event ID required after clustering')
        u=canonical_url(i.get('url'));require(u not in urls and i['event_id'] not in events,'duplicate candidate URL/event');urls.add(u);events.add(i['event_id'])
        require(i.get('decision') in ('main','radar','known','outdated','irrelevant','unverified'),'candidate decision required')
        require(text(i.get('reason'),500),'short factual selection reason required')
        if i.get('published_date'):day(i['published_date'])
        summary[i['category']]+=1
    if len(candidates)<cfg['discovery_candidate_target_min']:require(text(data.get('shortfall_reason'),800),'explain discovery shortfall; no invented candidates')
    return {'version':2,'checked_at':checked.isoformat(),'candidate_count':len(candidates),'coverage':summary,'checks_attempted':len(checks),'checks_successful':sum(c['outcome']=='success' for c in checks),'decisions':{d:sum(i['decision']==d for i in candidates) for d in ('main','radar','known','outdated','irrelevant','unverified')},'shortfall_reason':data.get('shortfall_reason'),'note':'Coverage records attempts, not universal absence of news. The full audit remains an artifact or scoped run log.'}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['plan','audit','lookup']);p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--date');p.add_argument('--input',type=Path);p.add_argument('--output',type=Path);p.add_argument('--event-id');a=p.parse_args()
    try:
        if a.command=='plan': result=plan(a.root,a.date)
        elif a.command=='lookup':result=load(a.root/'state/event-index.json')['events'].get(a.event_id)
        else: result=audit(a.root,load(a.input))
        if a.output:write_json(a.output,result)
        else:print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0
    except (ValueError,TypeError,KeyError,OSError) as e:print('ERROR:',e,file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
