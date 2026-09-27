"""Italian editorial bodies, stored separately from immutable edition payloads.

No scraping or model invocation: agents author original, source-checked content.
This module enforces structure and linkage, not factual/editorial correctness.
"""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker
from contracts import ID, load, require, section, settings, timestamp, url


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':')).encode('utf-8')).hexdigest()


def item_hash(item):
    """Invalidate stale bodies when the underlying reported facts change."""
    fields = ('id', 'event_id', 'title', 'summary', 'published_date', 'published_at',
              'event_date', 'status', 'delta', 'previous', 'sources')
    return digest({key: item.get(key) for key in fields})


def article_text(article):
    if not article:
        return ''
    return ' '.join(part for block in article['sections']
                    for part in [block['heading'], *block['paragraphs']])


def article_schema(cfg):
    limits = cfg['article_content']
    short = {'type': 'string', 'minLength': 1, 'maxLength': 160}
    urls = {'type': 'array', 'minItems': 1, 'maxItems': limits['max_sources'],
            'uniqueItems': True, 'items': {'type': 'string', 'pattern': '^https://'}}
    return {
        '$schema': 'https://json-schema.org/draft/2020-12/schema',
        'title': 'Personal News — Italian original article v1',
        'type': 'object', 'additionalProperties': False,
        'required': ['version', 'item_id', 'language', 'editorial_mode',
                     'source_item_hash', 'written_at', 'verified_at', 'sources', 'sections'],
        'properties': {
            'version': {'const': 1}, 'item_id': {'type': 'string', 'pattern': ID.pattern},
            'language': {'const': 'it'}, 'editorial_mode': {'const': 'original'},
            'source_item_hash': {'type': 'string', 'pattern': '^[a-f0-9]{64}$'},
            'written_at': {'type': 'string', 'format': 'date-time'},
            'verified_at': {'type': 'string', 'format': 'date-time'},
            'sources': {'type': 'array', 'minItems': 1, 'maxItems': limits['max_sources'],
                        'items': {'type': 'object', 'additionalProperties': False,
                                  'required': ['name', 'type', 'url'],
                                  'properties': {'name': short, 'type': {'enum': [
                                      'official', 'research', 'reputable', 'community']},
                                      'url': {'type': 'string', 'pattern': '^https://'}}}},
            'sections': {'type': 'array', 'minItems': limits['min_sections'],
                         'maxItems': limits['max_sections'],
                         'items': {'type': 'object', 'additionalProperties': False,
                                   'required': ['heading', 'paragraphs', 'source_urls'],
                                   'properties': {'heading': short,
                                       'paragraphs': {'type': 'array', 'minItems': 1,
                                           'maxItems': limits['max_paragraphs_per_section'],
                                           'items': {'type': 'string', 'minLength': 30,
                                                     'maxLength': limits['max_paragraph_chars']}},
                                       'source_urls': urls}}}
        }
    }


def validate_settings(cfg):
    limits = cfg.get('article_content')
    require(isinstance(limits, dict), 'article_content settings missing')
    for key in ('min_words_main', 'min_words_radar', 'max_words', 'min_sections',
                'max_sections', 'max_sources', 'max_paragraphs_per_section', 'max_paragraph_chars'):
        require(type(limits.get(key)) is int and limits[key] > 0,
                f'invalid article_content setting: {key}')
    require(limits['min_sections'] <= limits['max_sections'], 'invalid article section limits')
    require(max(limits['min_words_main'], limits['min_words_radar']) <= limits['max_words'],
            'invalid article word limits')
    return limits


def validate_article(article, item, cfg):
    limits = validate_settings(cfg)
    errors = list(Draft202012Validator(article_schema(cfg), format_checker=FormatChecker()).iter_errors(article))
    require(not errors, 'invalid Italian article schema: ' + (errors[0].message[:240] if errors else ''))
    require(article['item_id'] == item['id'], 'article/item identity mismatch')
    require(article['source_item_hash'] == item_hash(item), 'article is stale: source item hash mismatch')
    require(timestamp(article['verified_at']) <= timestamp(article['written_at']),
            'article verification after writing')
    source_urls = [s['url'] for s in article['sources']]
    require(len(source_urls) == len(set(source_urls)), 'duplicate article source')
    require(all(url(u) for u in source_urls), 'unsafe article source URL')
    require(any(u in {s['url'] for s in item['sources']} for u in source_urls),
            'article must cite at least one source of the news item')
    paragraphs = []
    for block in article['sections']:
        require(block['heading'].strip(), 'blank article heading')
        require(set(block['source_urls']) <= set(source_urls), 'unknown section citation')
        require(all(url(u) for u in block['source_urls']), 'unsafe section citation')
        for paragraph in block['paragraphs']:
            normalized = ' '.join(paragraph.split())
            require(len(normalized) >= 30, 'blank/short article paragraph')
            require(not re.fullmatch(r'(TODO|TBD|PLACEHOLDER)[.!\s]*', normalized, re.I),
                    'placeholder article')
            paragraphs.append(normalized)
    require(len(paragraphs) == len(set(paragraphs)), 'duplicate article paragraph')
    require(any(p != item['summary'].strip() for p in paragraphs), 'article only repeats summary')
    words = len(' '.join(paragraphs).split())
    minimum = limits['min_words_radar' if section(item) == 'radar' else 'min_words_main']
    require(minimum <= words <= limits['max_words'], f'article word count {words} outside {minimum}..{limits["max_words"]}')
    return words


def collect_articles(root, days):
    """Return validated bodies and deterministic metadata for every archived item."""
    root = Path(root)
    cfg = settings(root)
    validate_settings(cfg)
    legacy = load(root / 'config/ARTICLE_LEGACY.json')
    require(legacy.get('version') == 1 and isinstance(legacy.get('items'), dict),
            'invalid frozen article legacy manifest')
    by_id = {i['id']: (d, i) for d in days for i in d['items']}
    bodies, records = {}, []
    folder = root / 'docs/data/articles'
    for path in sorted(folder.glob('*.json')):
        require(path.stem in by_id, f'orphan article body: {path.name}')
        article = load(path)
        d, item = by_id[path.stem]
        words = validate_article(article, item, cfg)
        bodies[item['id']] = article
        records.append({'item_id': item['id'], 'edition': d.get('edition_id', d['date']),
                        'status': 'full', 'path': f'data/articles/{item["id"]}.json',
                        'word_count': words, 'written_at': article['written_at'],
                        'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    for item_id, (d, item) in sorted(by_id.items()):
        if item_id in bodies:
            continue
        receipt = legacy['items'].get(item_id)
        require(receipt == {'edition': d.get('edition_id', d['date']), 'sha256': digest(item)},
                f'Italian article required before publication: {item_id}')
        records.append({'item_id': item_id, 'edition': d.get('edition_id', d['date']),
                        'status': 'legacy_summary'})
    records.sort(key=lambda row: row['item_id'])
    return bodies, {'version': 1, 'items': records}


def main():
    import argparse
    from news import editions
    from contracts import ROOT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['describe'])
    parser.add_argument('--item-id', required=True)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    require(ID.fullmatch(args.item_id), 'invalid item ID')
    matches = [(d, i) for d in editions(args.root) for i in d['items'] if i['id'] == args.item_id]
    require(len(matches) == 1, 'item not found or not unique')
    d, item = matches[0]
    print(json.dumps({'item_id': item['id'], 'edition': d.get('edition_id', d['date']),
                      'article_path': f'docs/data/articles/{item["id"]}.json',
                      'source_item_hash': item_hash(item), 'sources': item['sources']},
                     ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
