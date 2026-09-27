#!/usr/bin/env python3
"""Extract an article's social image from an already downloaded HTML file.
No network access. Output is a candidate, not proof of reachability or a licence.
"""
import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import urljoin, urlsplit

class Meta(HTMLParser):
    def __init__(self):
        super().__init__(); self.tags = {}
    def handle_starttag(self, tag, attrs):
        if tag.lower() == 'meta':
            a = dict(attrs); key = a.get('property', a.get('name', '')).lower()
            if key not in self.tags and a.get('content'):
                self.tags[key] = a['content'].strip()

def extract(html, article_url):
    parser=Meta(); parser.feed(html)
    for key in ('og:image:secure_url','og:image','twitter:image','twitter:image:src'):
        candidate=urljoin(article_url, parser.tags.get(key,'')) if parser.tags.get(key) else ''
        parsed=urlsplit(candidate)
        if parsed.scheme=='https' and parsed.hostname and not parsed.username and not parsed.password:
            return {'url':candidate,'alt':parser.tags.get('og:image:alt',''),'source_url':article_url,'metadata_key':key,'verification':'Candidate from article metadata; verify image, relevance, credit and usage restrictions before publishing.'}
    return None

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('html',type=Path);p.add_argument('article_url');args=p.parse_args()
    print(json.dumps(extract(args.html.read_text(encoding='utf-8'),args.article_url),ensure_ascii=False,indent=2))
