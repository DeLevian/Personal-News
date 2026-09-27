import copy
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import news
from articles import article_schema, item_hash, validate_article, collect_articles
from article_fixtures import article, write_articles
from test_v2 import edition


class ArticleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / 'repo'
        shutil.copytree(news.ROOT, self.root, ignore=shutil.ignore_patterns('.git', 'artifacts', '__pycache__'))
        self.d = edition(main=1, radar=1)
        self.item = self.d['items'][0]
        self.a = article(self.item)
        self.cfg = news.load(self.root/'config/pipeline.json')

    def tearDown(self):
        self.tmp.cleanup()

    def save(self, body=True):
        news.write_json(self.root/f'docs/data/daily/{self.d["date"]}.json', self.d)
        if body: write_articles(self.root, self.d)

    def invalid(self):
        with self.assertRaises(news.Invalid): validate_article(self.a, self.item, self.cfg)

    def test_valid_italian_body(self):
        self.assertGreater(validate_article(self.a, self.item, self.cfg), 120)

    def test_new_item_requires_body(self):
        self.save(body=False)
        with self.assertRaisesRegex(news.Invalid, 'Italian article required'): news.run(self.root, 'rebuild')

    def test_radar_also_requires_body(self):
        self.save(); (self.root/f'docs/data/articles/{self.d["items"][-1]["id"]}.json').unlink()
        with self.assertRaisesRegex(news.Invalid, 'Italian article required'): news.run(self.root, 'rebuild')

    def test_wrong_language(self):
        self.a['language'] = 'en'; self.invalid()

    def test_copied_mode_not_accepted(self):
        self.a['editorial_mode'] = 'full_translation'; self.invalid()

    def test_mismatched_identity(self):
        self.a['item_id'] = 'different'; self.invalid()

    def test_stale_body_rejected(self):
        self.item['summary'] = 'A different factual claim.'; self.invalid()

    def test_hash_ignores_cosmetic_image_change(self):
        before = item_hash(self.item); self.item['image'] = None; self.item['featured'] = not self.item['featured']
        self.assertEqual(before, item_hash(self.item))

    def test_unsafe_source(self):
        self.a['sources'][0]['url'] = 'https://user:secret@example.com/a'; self.invalid()

    def test_unknown_citation(self):
        self.a['sections'][0]['source_urls'] = ['https://example.net/not-in-sources']; self.invalid()

    def test_no_section_citation(self):
        self.a['sections'][0]['source_urls'] = []; self.invalid()

    def test_duplicate_source(self):
        self.a['sources'].append(self.a['sources'][0]); self.invalid()

    def test_duplicate_paragraph(self):
        self.a['sections'][1]['paragraphs'] = self.a['sections'][0]['paragraphs']; self.invalid()

    def test_too_short(self):
        self.a['sections'][0]['paragraphs'] = ['Un testo corto non è un articolo autosufficiente.']
        self.a['sections'][1]['paragraphs'] = ['Questo secondo paragrafo rimane comunque troppo breve.']; self.invalid()

    def test_no_timestamp_offset(self):
        self.a['written_at'] = '2030-01-03T07:00:00'; self.invalid()

    def test_verification_after_writing(self):
        self.a['verified_at'] = '2030-01-04T07:00:00+01:00'; self.invalid()

    def test_orphan_body(self):
        self.save(); p=self.root/'docs/data/articles/orphan.json'; news.write_json(p,self.a)
        with self.assertRaisesRegex(news.Invalid, 'orphan'): news.run(self.root, 'rebuild')

    def test_index_search_and_idempotency(self):
        self.save(); news.run(self.root,'rebuild'); news.run(self.root,'validate')
        index=news.load(self.root/'docs/data/article-index.json')
        self.assertEqual(next(x for x in index['items'] if x['item_id']==self.item['id'])['status'],'full')
        row=next(x for x in news.load(self.root/'docs/data/search.json')['items'] if x['id']==self.item['id'])
        self.assertIn('archiviolettoreunico', row['search_text'])
        before=(self.root/'docs/data/index.json').read_bytes(); news.run(self.root,'rebuild')
        self.assertEqual(before,(self.root/'docs/data/index.json').read_bytes())

    def test_body_update_changes_revision_not_edition_dates(self):
        self.save(); news.run(self.root,'rebuild'); before=news.load(self.root/'docs/data/index.json')
        p=self.root/f'docs/data/articles/{self.item["id"]}.json'; a=news.load(p)
        a['sections'][0]['paragraphs'][0]+=' Una correzione editoriale verificata nel test.'; news.write_json(p,a)
        news.run(self.root,'rebuild'); after=news.load(self.root/'docs/data/index.json')
        self.assertNotEqual(before['content_revision'],after['content_revision'])
        self.assertEqual(before['updated_at'],after['updated_at'])
        self.assertEqual(self.d,news.load(self.root/f'docs/data/daily/{self.d["date"]}.json'))

    def test_legacy_payloads_remain_identical(self):
        paths=list((self.root/'docs/data/daily').glob('*.json'))+list((self.root/'docs/data/initial').glob('*.json'))
        before={p:p.read_bytes() for p in paths}; news.run(self.root,'rebuild')
        self.assertTrue(all(p.read_bytes()==data for p,data in before.items()))

    def test_invalid_configuration(self):
        self.cfg['article_content']['max_words']=1
        with self.assertRaises(news.Invalid): validate_article(self.a,self.item,self.cfg)


if __name__ == '__main__': unittest.main()
