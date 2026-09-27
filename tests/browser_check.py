"""Optional browser checks. pip install playwright; playwright install chromium.
Set CHROMIUM_PATH for a system Chromium. No external network is needed: external
images are deliberately aborted to test fallbacks. Extra dates stay in temp dirs.
"""
import copy
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from threading import Thread
from playwright.sync_api import sync_playwright, expect
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import news

class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass

def serve(path):
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(path)))
    Thread(target=server.serve_forever,daemon=True).start()
    return server,f'http://127.0.0.1:{server.server_port}/'

def main():
    out=news.ROOT/'artifacts';out.mkdir(exist_ok=True)
    server,base=serve(news.ROOT/'docs')
    results=[]
    with sync_playwright() as p:
        options={'headless':True}
        if os.environ.get('CHROMIUM_PATH'):options['executable_path']=os.environ['CHROMIUM_PATH']
        b=p.chromium.launch(**options)
        context=b.new_context(viewport={'width':1440,'height':1050},color_scheme='light')
        context.route('https://**/*',lambda route:route.abort())
        page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(base);expect(page.locator('.card')).to_have_count(6)
        expect(page.locator('#prev')).to_be_disabled();expect(page.locator('#next')).to_be_disabled()
        expect(page.locator('#edition-notice')).to_contain_text('Edizione iniziale')
        results.append('latest edition and truthful bootstrap/one-day boundaries')
        page.locator('#search').fill('Pi Agent');expect(page.locator('.card')).to_have_count(1)
        page.locator('#reset').click();expect(page.locator('.card')).to_have_count(6)
        page.locator('#chips button').filter(has_text='Microsoft').click();expect(page.locator('.card')).to_have_count(0);expect(page.locator('#empty')).to_be_visible()
        page.locator('#empty-reset').click();expect(page.locator('.card')).to_have_count(6)
        results.append('search/category filters and empty results')
        page.locator('.save-button').first.click();page.locator('#nav-saved').click();expect(page.locator('.card')).to_have_count(1)
        page.reload();expect(page.locator('.card')).to_have_count(1)
        page.locator('#latest-button').click();expect(page.locator('.card')).to_have_count(6)
        page.locator('#unread').click();page.locator('.read-button').first.click();expect(page.locator('.card')).to_have_count(5)
        page.locator('#read-all').click();expect(page.locator('.card')).to_have_count(0)
        page.locator('#reset').click();expect(page.locator('.card')).to_have_count(6)
        results.append('persistent saved/unread filters and mark-visible read')
        page.locator('#scope').select_option('archive');page.locator('#search').fill('Piktiv');expect(page.locator('.card')).to_have_count(1)
        page.locator('#latest-button').click();expect(page.locator('.card')).to_have_count(6)
        first_id=page.locator('.card').first.get_attribute('id')
        page.goto(base+'?date=2026-09-27#'+first_id);expect(page.locator('#'+first_id)).to_be_visible()
        page.goto(base+'?date=1999-01-01');expect(page.locator('.card')).to_have_count(6)
        results.append('archive search and permanent/missing-date links')
        page.locator('#nav-archive').click();expect(page.locator('#archive-dialog')).to_be_visible();page.locator('#archive-month').fill('2025-01');expect(page.locator('.archive-item')).to_have_count(0);page.keyboard.press('Escape');expect(page.locator('#archive-dialog')).not_to_be_visible()
        page.locator('#settings-open').click();page.locator('#theme-select').select_option('dark');expect(page.locator('html')).to_have_attribute('data-theme','dark');page.locator('#images').uncheck();expect(page.locator('body')).to_have_class('no-images');page.locator('#images').check();page.locator('#theme-select').select_option('light');page.keyboard.press('Escape')
        results.append('dialogs, month filter, themes and image preference')
        page.locator('#density').click();expect(page.locator('body')).to_have_class('compact');page.locator('#density').click()
        page.evaluate('localStorage.clear()');page.goto(base);expect(page.locator('.card')).to_have_count(6)
        page.wait_for_timeout(250)
        for width,height in [(1440,1050),(1024,900),(768,1024),(390,844),(320,740)]:
            page.set_viewport_size({'width':width,'height':height})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),f'horizontal overflow at {width}'
            if width in (1440,390):page.screenshot(path=str(out/f'preview-{width}.png'),full_page=True)
        results.append('no horizontal overflow at 1440/1024/768/390/320 px')
        page.set_viewport_size({'width':390,'height':844});page.locator('#mobile-archive').click();expect(page.locator('#archive-dialog')).to_be_visible();page.keyboard.press('Escape')
        page.locator('#mobile-saved').click();expect(page.locator('#empty')).to_be_visible();page.locator('#mobile-latest').click();expect(page.locator('.card')).to_have_count(6)
        results.append('mobile navigation')
        # A second edition exists only in a temporary copy, never in production.
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'repo';shutil.copytree(news.ROOT,root,ignore=shutil.ignore_patterns('.git','artifacts','__pycache__'))
            d=copy.deepcopy(news.editions(root)[0]);d['date']='2026-09-28';d['generated_at']='2026-09-28T07:00:00+02:00';d['items']=[];d['kind']='daily';d['summary']='Isolated navigation fixture';d['title']='Isolated test'
            news.write_json(root/'docs/data/daily/2026-09-28.json',d);news.run(root,'rebuild')
            second,url=serve(root/'docs')
            try:
                page.goto(url);expect(page.locator('#date-label')).to_contain_text('28 settembre');expect(page.locator('#prev')).to_be_enabled();page.locator('#prev').click();expect(page.locator('#date-label')).to_contain_text('27 settembre');expect(page.locator('.card')).to_have_count(6);expect(page.locator('#next')).to_be_enabled()
                page.go_back();expect(page.locator('#date-label')).to_contain_text('28 settembre');page.go_forward();expect(page.locator('#date-label')).to_contain_text('27 settembre');page.locator('#latest-button').click();expect(page.locator('#date-label')).to_contain_text('28 settembre')
                results.append('previous/next/latest and browser back/forward with isolated editions')
            finally:second.shutdown()
        assert not errors,errors
        results.append('zero JavaScript page errors; external-image fallback exercised')
        b.close()
    server.shutdown()
    (out/'browser-results.json').write_text(json.dumps({'checks':results,'external_images':'blocked on purpose; live image delivery not certified'},indent=2)+'\n')
    print(json.dumps(results,indent=2))
if __name__=='__main__':main()
