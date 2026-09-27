import copy
from datetime import timedelta
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import news
from image_metadata import extract

class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)/'repo'
        shutil.copytree(news.ROOT,self.root,ignore=shutil.ignore_patterns('__pycache__','.git','artifacts'))
        self.days=news.editions(self.root)
        self.base=copy.deepcopy(self.days[0])
        self.cats={c['id'] for c in news.load(self.root/'docs/data/categories.json')['categories']}
    def tearDown(self):
        self.temp.cleanup()
    def test_repository_valid(self):
        self.assertEqual(news.run(self.root,'validate'),0)
    def test_rebuild_idempotent(self):
        news.run(self.root,'rebuild')
        before=(self.root/'state/seen.json').read_bytes()
        news.run(self.root,'rebuild')
        self.assertEqual(before,(self.root/'state/seen.json').read_bytes())
    def test_unknown_category_rejected(self):
        self.base['items'][0]['category']='unknown'
        with self.assertRaises(news.Invalid):news.validate_edition(self.base,self.cats)
    def test_javascript_source_rejected(self):
        self.base['items'][0]['sources'][0]['url']='javascript:alert(1)'
        with self.assertRaises(news.Invalid):news.validate_edition(self.base,self.cats)
    def test_missing_image_credit_rejected(self):
        self.base['items'][0]['image'].pop('credit')
        with self.assertRaises(news.Invalid):news.validate_edition(self.base,self.cats)
    def test_duplicate_event_rejected(self):
        self.base['items'][1]['event_id']=self.base['items'][0]['event_id']
        with self.assertRaises(news.Invalid):news.validate_edition(self.base,self.cats)
    def test_old_items_cannot_be_daily(self):
        self.base['kind']='daily'
        with self.assertRaises(news.Invalid):news.validate_edition(self.base,self.cats)
    def test_invalid_item_is_controlled_error(self):
        self.base['items']=[None]
        with self.assertRaises(news.Invalid):news.validate_edition(self.base,self.cats)
    def test_missing_material_update_rejected(self):
        self.base['items'][0]['status']='UPDATE'
        with self.assertRaises(news.Invalid):news.validate_edition(self.base,self.cats)
    def test_valid_update_chain_and_date_navigation(self):
        d=copy.deepcopy(self.base);d['date']='2026-09-28';d['generated_at']='2026-09-28T07:00:00+02:00';d['items']=d['items'][:1]
        i=d['items'][0];old=i['id'];i['id']=i['id'].replace('2026-09-27','2026-09-28');i['status']='UPDATE';i['delta']='Test isolated update';i['summary']='A new fact for isolated tests';i['previous']={'id':old,'date':'2026-09-27'}
        news.write_json(self.root/'docs/data/daily/2026-09-28.json',d)
        news.run(self.root,'rebuild');news.run(self.root,'validate')
        m=news.load(self.root/'docs/data/index.json')
        self.assertEqual(m['latest'],'2026-09-28');self.assertEqual(len(m['editions']),2)
    def test_duplicate_new_in_later_edition_rejected(self):
        d=copy.deepcopy(self.base);d['date']='2026-09-28';d['generated_at']='2026-09-28T07:00:00+02:00'
        for i in d['items']:i['id']=i['id'].replace('2026-09-27','2026-09-28')
        news.write_json(self.root/'docs/data/daily/2026-09-28.json',d)
        with self.assertRaises(news.Invalid):news.editions(self.root)
    def test_stale_manifest_detected(self):
        news.write_json(self.root/'docs/data/index.json',{'version':1})
        with self.assertRaises(news.Invalid):news.run(self.root,'validate')
    def test_image_metadata_relative_url(self):
        r=extract('<meta property="og:image" content="/banner.jpg"><meta property="og:image:alt" content="Banner">','https://example.com/story')
        self.assertEqual(r['url'],'https://example.com/banner.jpg')
    def test_image_metadata_rejects_unsafe_url(self):
        self.assertIsNone(extract('<meta property="og:image" content="javascript:alert(1)">','https://example.com/story'))
    def test_empty_edition_supported(self):
        d=copy.deepcopy(self.base);d['items']=[];d['kind']='daily'
        news.validate_edition(d,self.cats)
if __name__=='__main__':unittest.main()
