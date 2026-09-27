"""Real HTTP/Chromium checks. Optional: Playwright. No fabricated archive dates.
Tests use the actual checked-out edition and isolated browser storage.
Images are blocked ONLY for the fallback test; live_check.py tests real delivery.
"""
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
import json, os
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass

def main():
    manifest=json.loads((ROOT/'docs/data/index.json').read_text())
    latest=manifest['editions'][0]
    daily=json.loads((ROOT/'docs'/latest['path']).read_text())
    n=len(daily['items'])
    out=ROOT/'artifacts';out.mkdir(exist_ok=True)
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT/'docs')))
    Thread(target=server.serve_forever,daemon=True).start()
    base=f'http://127.0.0.1:{server.server_port}/'
    results=[]
    try:
      with sync_playwright() as p:
        options={'headless':True}
        if os.environ.get('CHROMIUM_PATH'):options['executable_path']=os.environ['CHROMIUM_PATH']
        b=p.chromium.launch(**options)
        ctx=b.new_context(viewport={'width':1440,'height':1050},color_scheme='light')
        ctx.route('https://**/*',lambda route:route.fulfill(status=404,body='Image deliberately unavailable in fallback test'))
        page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(base);expect(page.locator('.card')).to_have_count(n)
        expect(page.locator('#unread')).to_have_attribute('aria-pressed','true')
        expect(page.locator('#next')).to_be_disabled()
        if len(manifest['editions'])>1:expect(page.locator('#prev')).to_be_enabled()
        results.append('initial latest edition and correct navigation boundaries')
        if n:
            first=daily['items'][0]
            page.locator('#search').fill(first['title']);expect(page.locator('.card')).to_have_count(1)
            page.locator('#reset').click();expect(page.locator('.card')).to_have_count(n)
            page.locator('#search').fill('this-search-intentionally-matches-no-article-98765');expect(page.locator('.card')).to_have_count(0)
            page.locator('#empty-reset').click();expect(page.locator('.card')).to_have_count(n)
            page.locator('.save-button').first.click();page.locator('#nav-saved').click();expect(page.locator('.card')).to_have_count(1)
            page.reload();expect(page.locator('.card')).to_have_count(1)
            page.locator('#latest-button').click();expect(page.locator('.card')).to_have_count(n);expect(page.locator('#unread')).to_have_attribute('aria-pressed','true')
            page.locator('.read-button').first.click();expect(page.locator('.card')).to_have_count(n-1)
            page.reload();expect(page.locator('.card')).to_have_count(n-1);expect(page.locator('#unread')).to_have_attribute('aria-pressed','true')
            page.locator('#unread').click();expect(page.locator('.card')).to_have_count(n)
            page.locator('#unread').click();expect(page.locator('.card')).to_have_count(n-1)
            page.locator('#read-all').click();expect(page.locator('.card')).to_have_count(0)
            page.locator('#reset').click();expect(page.locator('#unread')).to_have_attribute('aria-pressed','false');expect(page.locator('.card')).to_have_count(n)
            page.goto(base+'?date='+latest.get('id',latest['date'])+'#'+first['id'])
            expect(page.locator('[id="'+first['id']+'"]')).to_be_visible()
            results.append('search, empty results, saved across reload, unread, mark visible, permanent article links')
        page.goto(base+'?date=1999-01-01');expect(page.locator('.card')).to_have_count(n)
        page.locator('#nav-archive').click();expect(page.locator('#archive-dialog')).to_be_visible()
        page.locator('#archive-month').fill('1990-01');expect(page.locator('.archive-item')).to_have_count(0)
        page.keyboard.press('Escape');expect(page.locator('#archive-dialog')).not_to_be_visible()
        if len(manifest['editions'])>1:
            old=manifest['editions'][1];old_data=json.loads((ROOT/'docs'/old['path']).read_text())
            page.goto(base);page.locator('#prev').click()
            expect(page).to_have_url(base+'?date='+old.get('id',old['date']))
            expect(page.locator('.card')).to_have_count(len(old_data['items']))
            page.go_back();expect(page.locator('.card')).to_have_count(n)
            expect(page).to_have_url(base)
            page.go_forward();expect(page).to_have_url(base+'?date='+old.get('id',old['date']))
            page.locator('#next').click();expect(page).to_have_url(base)
            if old_data['items']:
                old_item=old_data['items'][0]
                page.goto(base+'?date='+old['date']+'#'+old_item['id'])
                expect(page.locator('[id="'+old_item['id']+'"]')).to_be_visible()
                page.locator('#scope').select_option('archive');page.locator('#search').fill(old_item['title'])
                expect(page.locator('.card')).to_have_count(1)
            results.append('previous/next, browser back/forward, same-day initial archive, old-link compatibility and global search')
        page.goto(base)
        page.locator('#settings-open').click();page.locator('#theme-select').select_option('dark')
        expect(page.locator('html')).to_have_attribute('data-theme','dark')
        page.locator('#images').uncheck();expect(page.locator('body')).to_have_class('no-images')
        page.locator('#images').check();page.locator('#theme-select').select_option('light');page.keyboard.press('Escape')
        page.locator('#density').click();expect(page.locator('body')).to_have_class('compact');page.locator('#density').click()
        results.append('dialogs, theme, image preference and compact mode')
        page.evaluate('localStorage.clear()');page.goto(base);expect(page.locator('.card')).to_have_count(n)
        for width,height in [(1440,1050),(1024,900),(768,1024),(390,844),(320,740)]:
            page.set_viewport_size({'width':width,'height':height})
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),f'Horizontal overflow at {width}'
            if width in (1440,390):page.screenshot(path=str(out/f'fallback-{width}.png'),full_page=True)
        results.append('five responsive widths without overflow and external image fallback')
        page.set_viewport_size({'width':390,'height':844});page.locator('#mobile-archive').click()
        expect(page.locator('#archive-dialog')).to_be_visible();page.keyboard.press('Escape')
        page.locator('#mobile-saved').click();expect(page.locator('#empty')).to_be_visible()
        page.locator('#mobile-latest').click();expect(page.locator('.card')).to_have_count(n)
        assert not errors,errors
        results.append('mobile navigation and zero JavaScript errors')
        ctx.unroute_all(behavior='wait');ctx.close();b.close()
    finally:server.shutdown()
    evidence={'result':'passed','checks':results,'latest_count':n,'archive_count':len(manifest['editions'])}
    (out/'browser-results.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print('BROWSER_RESULT '+json.dumps(evidence))
if __name__=='__main__':main()
