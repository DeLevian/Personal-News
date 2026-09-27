"""Isolated fixtures only: these articles must never be published to docs/."""
import copy, json, shutil, sys, tempfile, unittest
from datetime import datetime,timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import news,discovery,briefing
from contracts import CATEGORIES,counts,make_schema

def edition(date='2030-01-03',main=1,radar=1):
    now=datetime.fromisoformat(date+'T07:00:00').replace(tzinfo=ZoneInfo('Europe/Rome'))
    data={'version':2,'date':date,'generated_at':now.isoformat(),'kind':'daily','title':'ISOLATED TEST','summary':'Fixture: never publish.','items':[]}
    for n in range(main+radar):
        sec='main' if n<main else 'radar';pub=now-timedelta(hours=2)
        data['items'].append({'id':f'{date}-fixture-{n}','event_id':f'fixture-{date}-{n}','section':sec,'status':'NEW','category':'ai' if sec=='main' else 'gamedev','title':f'{sec} fixture {n}','summary':'Verified only as a synthetic software test.','why_you_care':'Fixture only.','published_date':pub.date().isoformat(),'published_at':pub.isoformat(),'event_date':pub.date().isoformat(),'verified_at':now.isoformat(),'included_at':now.isoformat(),'featured':sec=='main' and n<3,'tags':['fixture'],'sources':[{'name':'Fixture','type':'official','url':f'https://example.com/news/{n}'}],'image':None})
    return data

def attention(d):
    now=news.timestamp(d['generated_at'])
    d['attention_today']={'text':'Fixture deadline','item_ids':[d['items'][0]['id']],'source_url':d['items'][0]['sources'][0]['url'],'valid_from':(now-timedelta(hours=1)).isoformat(),'expires_at':(now+timedelta(hours=3)).isoformat()}
    return d

class V2Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)/'repo'
        shutil.copytree(news.ROOT,self.root,ignore=shutil.ignore_patterns('.git','__pycache__','artifacts','_migration'))
        self.d=edition()
    def tearDown(self):self.temp.cleanup()
    def valid(self,d=None):return news.validate_edition(d or self.d,CATEGORIES,self.root)
    def bad(self,d=None):
        with self.assertRaises((news.Invalid,ValueError)):self.valid(d)
    def test_v2_valid(self):self.valid()
    def test_legacy_archive_valid(self):self.assertTrue(news.editions(self.root))
    def test_empty_v2(self):self.valid(edition(main=0,radar=0))
    def test_main_limit_16(self):self.valid(edition(main=16,radar=0));self.bad(edition(main=17,radar=0))
    def test_radar_limit_8(self):self.valid(edition(main=0,radar=8));self.bad(edition(main=0,radar=9))
    def test_featured_only_main(self):self.d['items'][-1]['featured']=True;self.bad()
    def test_featured_limit(self):d=edition(main=4,radar=0);d['items'][-1]['featured']=True;self.bad(d)
    def test_explicit_section_required(self):del self.d['items'][0]['section'];self.bad()
    def test_unknown_section(self):self.d['items'][0]['section']='ad';self.bad()
    def test_main_24h_reason(self):
        i=self.d['items'][0];pub=news.timestamp(i['included_at'])-timedelta(hours=25);i.update(published_at=pub.isoformat(),published_date=pub.date().isoformat());self.bad();i['recency_reason']='Material update recovered';self.valid()
    def test_main_72h_boundary(self):
        i=self.d['items'][0];pub=news.timestamp(i['included_at'])-timedelta(hours=72);i.update(published_at=pub.isoformat(),published_date=pub.date().isoformat(),recency_reason='Material recovered news');self.valid();i['published_at']=(pub-timedelta(seconds=1)).isoformat();i['published_date']=(pub-timedelta(seconds=1)).date().isoformat();self.bad()
    def test_radar_7_days_boundary(self):
        i=self.d['items'][-1];pub=news.timestamp(i['included_at'])-timedelta(days=7);i.update(published_at=pub.isoformat(),published_date=pub.date().isoformat());self.valid();i['published_at']=(pub-timedelta(seconds=1)).isoformat();i['published_date']=(pub-timedelta(seconds=1)).date().isoformat();self.bad()
    def test_unknown_publication_not_today(self):self.d['items'][0]['published_date']=None;self.bad()
    def test_future_publication(self):i=self.d['items'][0];i['published_at']=self.d['date']+'T20:00:00+01:00';self.bad()
    def test_timezone_generation(self):self.d['generated_at']='2030-01-03T23:30:00-04:00';self.bad()
    def test_same_day_included_at_preserved(self):self.d['generated_at']='2030-01-03T23:00:00+01:00';self.valid()
    def test_attention_valid(self):self.valid(attention(self.d))
    def test_attention_missing_item(self):attention(self.d)['attention_today']['item_ids']=['missing'];self.bad()
    def test_attention_unrelated_source(self):attention(self.d)['attention_today']['source_url']='https://example.org/no';self.bad()
    def test_attention_expired(self):attention(self.d)['attention_today']['expires_at']=self.d['generated_at'];self.bad()
    def test_attention_invalid_https(self):attention(self.d)['attention_today']['source_url']='javascript:bad()';self.bad()
    def test_blank_text(self):self.d['items'][0]['summary']=' ';self.bad()
    def test_source_url_security(self):self.d['items'][0]['sources'][0]['url']='https://user:pass@example.com';self.bad()
    def test_image_null_valid(self):self.valid()
    def test_image_metadata_required(self):self.d['items'][0]['image']={'url':'https://example.com/i.png'};self.bad()
    def test_totals_consistent(self):c=counts(self.d['items']);self.assertEqual(c['main']+c['radar'],c['new']+c['update'])
    def save(self,d):news.write_json(self.root/f'docs/data/daily/{d["date"]}.json',d)
    def test_radar_to_main_new_rejected(self):
        a=edition(main=0,radar=1);b=edition('2030-01-04',main=1,radar=0);b['items'][0]['event_id']=a['items'][0]['event_id'];self.save(a);self.save(b)
        with self.assertRaises(news.Invalid):news.editions(self.root)
    def test_cross_section_update_valid(self):
        a=edition(main=0,radar=1);b=edition('2030-01-04',main=1,radar=0);i=b['items'][0];i.update(event_id=a['items'][0]['event_id'],status='UPDATE',summary='A genuinely different fixture fact.',delta='New fact, not a change of layout.',previous={'id':a['items'][0]['id'],'date':a['date']});self.save(a);self.save(b);news.run(self.root,'rebuild');news.run(self.root,'validate')
    def test_cache_eviction_does_not_reset_event(self):
        a=edition(main=0,radar=1);b=edition('2030-03-04',main=1,radar=0);b['items'][0]['event_id']=a['items'][0]['event_id'];self.save(a);self.save(b)
        with self.assertRaises(news.Invalid):news.editions(self.root)
    def test_search_includes_both_sections(self):self.save(self.d);news.run(self.root,'rebuild');items=news.load(self.root/'docs/data/search.json')['items'];self.assertEqual({i['section'] for i in items if i['edition']==self.d['date']},{'main','radar'})
    def test_rebuild_idempotent(self):news.run(self.root,'rebuild');a=(self.root/'docs/data/index.json').read_bytes();news.run(self.root,'rebuild');self.assertEqual(a,(self.root/'docs/data/index.json').read_bytes())
    def test_sources_contract(self):news.validate_catalogue(self.root)
    def mutate_sources(self,fn):
        path=self.root/'config/SOURCES.json';d=news.load(path);fn(d);news.write_json(path,d)
        with self.assertRaises(news.Invalid):news.validate_catalogue(self.root)
    def test_duplicate_source_ids(self):self.mutate_sources(lambda d:d['sources'].append(d['sources'][0]))
    def test_source_http_rejected(self):self.mutate_sources(lambda d:d['sources'][0].update(url='http://example.com'))
    def test_source_bad_tier(self):self.mutate_sources(lambda d:d['sources'][0].update(tier=4))
    def test_source_role_mismatch(self):self.mutate_sources(lambda d:d['sources'][0].update(role='scouting'))
    def test_source_policy(self):self.mutate_sources(lambda d:d['sources'][0].update(check_policy='never'))
    def test_ui_sources_not_duplicated(self):
        path=self.root/'docs/data/categories.json';d=news.load(path);d['categories'][0]['topics']=['oops'];news.write_json(path,d)
        with self.assertRaises(news.Invalid):news.validate_catalogue(self.root)
    def test_rotation_and_coverage(self):
        a=discovery.plan(self.root,'2030-01-03');b=discovery.plan(self.root,'2030-01-04');self.assertEqual(set(a['categories']),CATEGORIES);self.assertNotEqual(a['categories']['ai']['check_first'],b['categories']['ai']['check_first']);self.assertEqual(a,discovery.plan(self.root,'2030-01-03'))
    def test_tracking_url_dedup(self):self.assertEqual(discovery.canonical_url('https://example.com/a?utm_source=x&k=1#fragment'),'https://example.com/a?k=1')
    def test_incomplete_discovery_is_not_success(self):
        with self.assertRaises(news.Invalid):discovery.audit(self.root,{'version':2,'checked_at':self.d['generated_at'],'checks':[],'candidates':[]})
    def test_shortfall_needs_explanation(self):
        d={'version':2,'checked_at':self.d['generated_at'],'checks':[{'category':c,'method':'web_search','query':c+' news','outcome':'no_results','evidence':'Isolated fixture'} for c in CATEGORIES],'candidates':[]}
        with self.assertRaises(news.Invalid):discovery.audit(self.root,d)
        d['shortfall_reason']='Isolated empty result test';self.assertEqual(discovery.audit(self.root,d)['candidate_count'],0)
    def test_briefing_bounded_and_truthful(self):
        d=attention(edition(main=3,radar=4));result=briefing.render(d,'https://example.com/',now=news.timestamp(d['generated_at']));self.assertLessEqual(len(result.splitlines()),10);self.assertIn('3 News · 4 Radar · 7 NEW · 0 UPDATE',result);self.assertIn('non verificato',result);self.assertIn('Da sapere oggi',result)
    def test_briefing_expired_attention_hidden(self):
        d=attention(self.d);result=briefing.render(d,'https://example.com/',now=news.timestamp(d['generated_at'])+timedelta(days=1));self.assertNotIn('Da sapere oggi:',result)
if __name__=='__main__':unittest.main()
