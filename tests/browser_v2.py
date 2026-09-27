"""Exercise v2 on a temporary copy. No synthetic edition enters the published archive."""
import json,os,shutil,tempfile,sys
from pathlib import Path
from threading import Thread
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright,expect
from test_v2 import edition,attention
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import news
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass

def main():
 out=news.ROOT/'artifacts';out.mkdir(exist_ok=True)
 original={str(p.relative_to(news.ROOT)):p.read_bytes() for folder in ('daily','initial') for p in (news.ROOT/f'docs/data/{folder}').glob('*.json')}
 checks=[]
 with tempfile.TemporaryDirectory() as tmp:
  root=Path(tmp)/'repo';shutil.copytree(news.ROOT,root,ignore=shutil.ignore_patterns('.git','artifacts','__pycache__','_migration'))
  d=attention(edition(main=3,radar=2));d['items'][-1]['image']={'url':'https://example.com/preview.svg','alt':'Synthetic test image','credit':'Test fixture','source_url':'https://example.com/news/4'}
  d['items'][0]['title']='<img src=x onerror=window.fixtureXSS=true> main fixture'
  news.write_json(root/f'docs/data/daily/{d["date"]}.json',d);news.run(root,'rebuild')
  manifest=news.load(root/'docs/data/index.json')
  previous=news.load(root/'docs'/manifest['editions'][1]['path'])
  server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(root/'docs')));Thread(target=server.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{server.server_port}/'
  try:
   with sync_playwright() as p:
    opts={'headless':True}
    if os.environ.get('CHROMIUM_PATH'):opts['executable_path']=os.environ['CHROMIUM_PATH']
    b=p.chromium.launch(**opts);ctx=b.new_context(viewport={'width':1440,'height':1000},color_scheme='light')
    ctx.add_init_script("const RealDate=Date;globalThis.Date=class extends RealDate{constructor(...args){super(...(args.length?args:['2030-01-03T08:00:00+01:00']));}static now(){return new RealDate('2030-01-03T08:00:00+01:00').getTime();}}");ctx.route('https://**/*',lambda r:r.fulfill(status=200,content_type='image/svg+xml',body='<svg xmlns="http://www.w3.org/2000/svg" width="80" height="40"><rect width="80" height="40" fill="gray"/></svg>'))
    page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(base);expect(page.locator('#cards .card')).to_have_count(3);expect(page.locator('#radar-cards .card')).to_have_count(2);expect(page.locator('#attention-today')).to_be_visible();expect(page.locator('#metrics')).to_contain_text('3News');expect(page.locator('#metrics')).to_contain_text('2Radar');assert not page.evaluate('window.fixtureXSS===true');checks.append('v2 main/radar, consistent counters, attention and XSS text safety')
    page.locator('[data-section-filter=radar]').click();expect(page.locator('.card')).to_have_count(2);expect(page.locator('#main-group')).to_be_hidden();page.reload();expect(page.locator('.card')).to_have_count(2)
    page.locator('.save-button').first.click();page.locator('#saved').click();expect(page.locator('.card')).to_have_count(1);page.locator('#reset').click();expect(page.locator('.card')).to_have_count(5)
    page.locator('[data-section-filter=main]').click();expect(page.locator('.card')).to_have_count(3);page.locator('#unread').click();page.locator('.read-button').first.click();expect(page.locator('.card')).to_have_count(2);page.locator('#reset').click()
    page.locator('#scope').select_option('archive');page.locator('#search').fill('radar fixture');expect(page.locator('.card')).to_have_count(2);page.locator('#latest-button').click();expect(page.locator('.card')).to_have_count(5);checks.append('section/category/read/saved filters, reload and cross-archive search')
    page.locator('#radar-cards .image-expand').click();expect(page.locator('#image-dialog')).to_be_visible();page.wait_for_function('document.getElementById("full-image").naturalWidth>0');page.keyboard.press('Escape');expect(page.locator('#image-dialog')).to_be_hidden();checks.append('Radar image and lightbox')
    radar=d['items'][-1];page.goto(base+'?date='+d['date']+'&section=main#'+radar['id']);expect(page.locator('[id="'+radar['id']+'"]')).to_be_visible();checks.append('permanent Radar link clears conflicting section filter')
    page.locator('#density').click();expect(page.locator('.radar-card .why').first).to_be_visible();page.locator('#density').click()
    for w,h in [(1440,1000),(1024,900),(768,1024),(390,844),(320,740)]:
     page.set_viewport_size({'width':w,'height':h});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),f'overflow {w}'
     if w in (1440,390):page.screenshot(path=str(out/f'v2-fixture-{w}.png'),full_page=True)
    page.locator('#mobile-archive').click();expect(page.locator('#archive-dialog')).to_be_visible();page.keyboard.press('Escape');page.locator('#prev').click()
    expect(page.locator('#date-label')).not_to_contain_text('2030')
    if previous.get('attention_today'):
     expect(page.locator('#attention-today')).to_contain_text('DA SAPERE ALLORA · ARCHIVIO')
    else:
     expect(page.locator('#attention-today')).to_be_hidden()
    page.locator('#latest-button').click();expect(page.locator('#radar-cards .card')).to_have_count(2);checks.append('historic attention labelled as archive; mobile navigation and 5 responsive widths')
    expired=b.new_context();expired.add_init_script("const R=Date;globalThis.Date=class extends R{constructor(...a){super(...(a.length?a:['2030-01-03T12:00:00+01:00']));}static now(){return new R('2030-01-03T12:00:00+01:00').getTime();}}")
    expired.route('https://**/*',lambda r:r.fulfill(status=404,body='fallback fixture'));ep=expired.new_page();ep.goto(base);expect(ep.locator('#attention-today')).to_be_hidden();expect(ep.locator('.card')).to_have_count(5);checks.append('expired attention hidden and unavailable-image fallback')
    assert not errors,errors;expired.close();ctx.unroute_all(behavior='wait');ctx.close();b.close()
  finally:server.shutdown()
 assert all((news.ROOT/k).read_bytes()==v for k,v in original.items()),'test mutated production archive'
 report={'result':'passed','checks':checks,'archive_unchanged':True,'synthetic_data':'temporary copy only'};(out/'v2-browser-results.json').write_text(json.dumps(report,indent=2)+'\n');print('V2_BROWSER '+json.dumps(report))
if __name__=='__main__':main()
