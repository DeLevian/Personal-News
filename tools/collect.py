#!/usr/bin/env python3
"""Bounded, read-only metadata discovery. Candidates are NOT verified news.
Fetch configured public indexes, parse their links, then let the agent verify articles.
Does not mutate registry, editions, or source state.
"""
from __future__ import annotations
import argparse,json,re,sys,hashlib
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urljoin,urlsplit
from urllib.request import Request,urlopen
from zoneinfo import ZoneInfo
from contracts import ROOT,url,validate_catalogue
from discovery import canonical_url,plan
from news import write_json
class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[];self.current=None;self.parts=[];self.title=[];self.in_title=False
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='title':self.in_title=True
        if tag=='a' and a.get('href'):
            self.current=a['href'];self.parts=[]
    def handle_data(self,text):
        if self.current:self.parts.append(text)
        if self.in_title:self.title.append(text)
    def handle_endtag(self,tag):
        if tag=='a' and self.current:
            self.links.append((self.current,' '.join(' '.join(self.parts).split())));self.current=None
        if tag=='title':self.in_title=False

def probe(s,timeout=15):
    record={'source_id':s['id'],'category':s['category'],'url':s['url'],'checked_at':datetime.now(ZoneInfo('Europe/Rome')).isoformat(timespec='seconds'),'status':'error','candidates':[]}
    try:
        request=Request(s['url'],headers={'User-Agent':'PersonalNews/2.0 (public editorial index check)'})
        with urlopen(request,timeout=timeout) as r:
            final=r.geturl()
            if not url(final):raise ValueError('Non-HTTPS redirect rejected')
            body=r.read(2_000_001)
            record.update(http_status=r.status,final_url=canonical_url(final),bytes_sampled=len(body),sample_sha256=hashlib.sha256(body).hexdigest())
        parser=Links();parser.feed(body.decode('utf-8','replace'))
        title=' '.join(parser.title).strip();record['title']=title[:200]
        if re.search(r'just a moment|access denied|robot or human|security check|attention required',title,re.I):
            record['status']='blocked';return record
        record['status']='reachable'
        seen=set()
        for href,title in parser.links:
            target=urljoin(final,href)
            if not url(target) or len(title)<18 or len(title)>240:continue
            target=canonical_url(target);path=urlsplit(target).path.lower()
            if target in seen or target==canonical_url(final):continue
            if not any(part in path for part in ['/blog/','/news/','/articles/','/article/','/posts/','/releases/tag/','/2026/','/2025/','/viewtopic.php']):continue
            if any(part in path for part in ['/category/','/author/','/privacy','/terms','/login','/search','/page/']) or ('/tag/' in path and '/releases/tag/' not in path):continue
            seen.add(target)
            record['candidates'].append({'title':title,'url':target,'category':s['category'],'source_id':s['id'],'discovered_at':record['checked_at'],'verification':'unverified','date_hint':next(iter(re.findall(r'20\d{2}[-/]\d{2}[-/]\d{2}',target)),None)})
            if len(record['candidates'])>=16:break
    except HTTPError as e:record.update(status='blocked' if e.code in (401,403,429) else 'error',http_status=e.code,error=str(e)[:200])
    except Exception as e:record['error']=str(e)[:200]
    return record

def collect(root,when,health=False):
    cfg,catalogue=validate_catalogue(root)
    if health:sources=catalogue['sources']
    else:
        p=plan(root,when);sources=[]
        for c in p['categories'].values():sources+=c['check_first']+c['on_gap'][:1]
    records=list(ThreadPoolExecutor(max_workers=4).map(probe,sources))
    bycat={k:[] for k in sorted(catalogue['query_matrix'])};seen=set()
    for r in records:
        for c in r['candidates']:
            if c['url'] not in seen:bycat[c['category']].append(c);seen.add(c['url'])
    pool=[]
    while any(bycat.values()) and len(pool)<cfg['discovery_candidate_target_max']:
        for category in bycat:
            if bycat[category] and len(pool)<cfg['discovery_candidate_target_max']:pool.append(bycat[category].pop(0))
    return {'version':2,'date':when,'mode':'source_health' if health else 'metadata_discovery','candidate_count':len(pool),'checks':[{k:v for k,v in r.items() if k!='candidates'} for r in records],'candidates':pool,'note':'Real retrieved index links, not verified facts or automatically selected articles. Blocked/empty indexes require open web search. Complete editorial audit before publication.'}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--date',required=True);p.add_argument('--health',action='store_true');p.add_argument('--output',type=Path,default=ROOT/'artifacts/discovery.json');a=p.parse_args()
    result=collect(ROOT,a.date,a.health);write_json(a.output,result)
    print(json.dumps({'candidate_count':result['candidate_count'],'checks':len(result['checks']),'reachable':sum(r['status']=='reachable' for r in result['checks']),'output':str(a.output),'scope':result['mode']}))
if __name__=='__main__':main()
