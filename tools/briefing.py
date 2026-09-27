#!/usr/bin/env python3
"""Deterministic morning briefing. Never infer a successful deployment."""
import argparse
from datetime import datetime
from zoneinfo import ZoneInfo
from contracts import ROOT,load,counts,timestamp
from news import editions

def render(d,site,git_status='non verificato',pages_status='non verificato',now=None):
    now=now or datetime.now(ZoneInfo('Europe/Rome'));c=counts(d['items'])
    lines=[f"Personal News · {d['date']}",f"{c['main']} News · {c['radar']} Radar · {c['new']} NEW · {c['update']} UPDATE · {c['featured']} Da non perdere"]
    featured=[i for i in d['items'] if i['featured']][:3]
    if featured:
        lines.append('Da non perdere:')
        lines += ['— '+i['title'] for i in featured]
    if not d['items']:lines.append('Nessuna novità verificata da pubblicare; nessun riempitivo.')
    a=d.get('attention_today')
    if a and d['date']==now.astimezone(ZoneInfo('Europe/Rome')).date().isoformat() and timestamp(a['valid_from'])<=now<timestamp(a['expires_at']):lines.append('Da sapere oggi: '+a['text'])
    lines.extend([f'GitHub: {git_status} · Pages: {pages_status}',site])
    return '\n'.join(lines)
def main():
    p=argparse.ArgumentParser();p.add_argument('--edition');p.add_argument('--git-status',default='non verificato');p.add_argument('--pages-status',default='non verificato');a=p.parse_args()
    d=load(ROOT/a.edition) if a.edition else editions(ROOT)[-1]
    print(render(d,load(ROOT/'config/pipeline.json')['website_url'],a.git_status,a.pages_status))
if __name__=='__main__':main()
