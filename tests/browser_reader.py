"""HTTP browser regressions for the reader, using isolated synthetic bodies only."""
import json
import os
import shutil
import tempfile
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright, expect
from test_v2 import edition
from article_fixtures import write_articles
import news


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args): pass


def main():
    out = news.ROOT/'artifacts'; out.mkdir(exist_ok=True)
    production = {str(p.relative_to(news.ROOT)): p.read_bytes()
                  for p in (news.ROOT/'docs/data').rglob('*.json')}
    checks = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)/'repo'
        shutil.copytree(news.ROOT, root, ignore=shutil.ignore_patterns('.git', 'artifacts', '__pycache__'))
        manifest = news.load(root/'docs/data/index.json')
        legacy = news.load(root/'config/ARTICLE_LEGACY.json')
        old_id, receipt = next(iter(legacy['items'].items()))
        old_edition = next(e for e in manifest['editions'] if e['id'] == receipt['edition'])
        old = next(i for i in news.load(root/'docs'/old_edition['path'])['items'] if i['id'] == old_id)
        # An exact pre-reader payload is the only permitted summary fallback.
        (root/f'docs/data/articles/{old["id"]}.json').unlink(missing_ok=True)
        d = edition(main=1, radar=1)
        d['items'][0]['image'] = {'url': 'https://example.com/reader.svg', 'alt': 'Fixture immagine',
            'credit': 'Fixture', 'source_url': d['items'][0]['sources'][0]['url']}
        news.write_json(root/f'docs/data/daily/{d["date"]}.json', d); write_articles(root, d)
        first = d['items'][0]; second = d['items'][1]
        body_path = root/f'docs/data/articles/{first["id"]}.json'
        body = news.load(body_path)
        body['sections'][0]['paragraphs'][0] += ' Ricercasolograndetesto è presente soltanto nell’articolo.'
        news.write_json(body_path, body); news.run(root, 'rebuild')
        server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Quiet, directory=str(root/'docs')))
        Thread(target=server.serve_forever, daemon=True).start()
        base = f'http://127.0.0.1:{server.server_port}/'
        shared = base+f'?date={d["date"]}&article={first["id"]}'
        try:
            with sync_playwright() as p:
                opts = {'headless': True}
                if os.environ.get('CHROMIUM_PATH'): opts['executable_path'] = os.environ['CHROMIUM_PATH']
                browser = p.chromium.launch(**opts)
                ctx = browser.new_context(viewport={'width': 1440, 'height': 1000}, color_scheme='light',
                                          permissions=['clipboard-read', 'clipboard-write'])
                ctx.route('https://**/*', lambda r: r.fulfill(status=200, content_type='image/svg+xml',
                          body='<svg xmlns="http://www.w3.org/2000/svg" width="160" height="80"><rect width="160" height="80" fill="gray"/></svg>'))
                page = ctx.new_page(); errors = []; page.on('pageerror', lambda e: errors.append(str(e)))
                dialog = page.locator('#reader-dialog')
                page.goto(base); expect(page.locator('.card')).to_have_count(2)
                arrow = page.locator('[id="'+first['id']+'"] .read-story-button')
                arrow.scroll_into_view_if_needed(); before_url = page.url; before_y = page.evaluate('scrollY')
                arrow.click(); expect(dialog).to_be_visible(); expect(dialog).to_have_attribute('data-content-status', 'full')
                expect(page.locator('#reader-body')).to_contain_text('Ricercasolograndetesto')
                expect(page.locator('#reader-title')).to_have_text(first['title'])
                assert 'article='+first['id'] in page.url
                page.locator('#reader-back').click(); expect(dialog).to_be_hidden(); expect(page).to_have_url(before_url)
                assert abs(page.evaluate('scrollY')-before_y) < 3
                assert page.locator('[id="'+first['id']+'"] .read-story-button').evaluate('(b)=>b===document.activeElement')
                checks.append('arrow opens full Italian article; close restores URL, scroll and focus')

                arrow.click(); expect(dialog).to_have_attribute('data-content-status', 'full')
                page.locator('#reader-save').click(); expect(page.locator('#reader-save')).to_have_attribute('aria-pressed', 'true')
                page.locator('#reader-read').click(); expect(page.locator('#reader-read')).to_have_attribute('aria-pressed', 'true')
                page.locator('#reader-share').click(); copied = page.evaluate('navigator.clipboard.readText()')
                assert copied == shared, copied
                with page.expect_popup() as popup:
                    page.locator('#reader-sources a').first.click()
                expect(popup.value).to_have_url(first['sources'][0]['url']); popup.value.close()
                expect(dialog).to_be_visible()
                page.keyboard.press('Escape'); expect(dialog).to_be_hidden(); expect(page.locator('.card')).to_have_count(1)
                page.reload(); expect(page.locator('.card')).to_have_count(1)
                data = page.evaluate("JSON.parse(localStorage.getItem('personal-news.v1'))")
                assert first['id'] in data['read'] and first['id'] in data['saved']
                checks.append('reader read/saved share the existing store; source stays external; sharing opens reader')

                page.goto(shared); expect(dialog).to_have_attribute('data-content-status', 'full')
                page.reload(); expect(dialog).to_have_attribute('data-content-status', 'full')
                page.keyboard.press('Escape'); expect(dialog).to_be_hidden(); assert 'article=' not in page.url
                page.evaluate('localStorage.clear()'); page.goto(base)
                page.locator('#search').fill('Ricercasolograndetesto'); expect(page.locator('.card')).to_have_count(1)
                page.locator('#scope').select_option('archive'); expect(page.locator('.card')).to_have_count(1)
                page.locator('.read-story-button').click(); expect(dialog).to_have_attribute('data-content-status', 'full')
                page.go_back(); expect(dialog).to_be_hidden(); expect(page.locator('#search')).to_have_value('Ricercasolograndetesto')
                page.go_forward(); expect(dialog).to_have_attribute('data-content-status', 'full')
                checks.append('deep link/reload/back/forward and full-body search in edition and archive')

                page.goto(base+'?date='+receipt['edition']+'&article='+old['id'])
                expect(dialog).to_have_attribute('data-content-status', 'legacy-summary')
                expect(page.locator('#reader-status')).to_contain_text('scheda storica')
                page.goto(base+'?date='+receipt['edition']+'#'+old['id'])
                expect(page.locator('[id="'+old['id']+'"]')).to_be_visible(); expect(dialog).to_be_hidden()
                checks.append('historical summary explicitly labelled; old hash links preserved')

                pattern = '**/data/articles/'+first['id']+'.json'
                page.route(pattern, lambda r: r.fulfill(status=503, body='Temporary test outage'))
                page.goto(shared); expect(dialog).to_have_attribute('data-content-status', 'error')
                expect(page.locator('#reader-retry')).to_be_visible()
                page.unroute(pattern); page.locator('#reader-retry').click(); expect(dialog).to_have_attribute('data-content-status', 'full')
                hostile = json.loads(json.dumps(body))
                hostile['sections'][0]['paragraphs'][0] = '<img id="injected-reader" src=x onerror="window.readerXSS=true"> '+hostile['sections'][0]['paragraphs'][0]
                page.route(pattern, lambda r: r.fulfill(json=hostile))
                page.reload(); expect(dialog).to_have_attribute('data-content-status', 'full')
                expect(page.locator('#reader-body')).to_contain_text('<img id="injected-reader"')
                assert page.locator('#injected-reader').count() == 0 and not page.evaluate('window.readerXSS===true')
                page.unroute(pattern)
                hostile['sources'][0]['url']='javascript:window.readerXSS=true'
                page.route(pattern, lambda r: r.fulfill(json=hostile))
                page.reload(); expect(dialog).to_have_attribute('data-content-status', 'error')
                assert not page.evaluate('window.readerXSS===true'); page.unroute(pattern)
                checks.append('HTTP errors and retry; malicious text escaped; unsafe links rejected')

                held = []
                page.route(pattern, lambda r: held.append(r))
                page.goto(shared); expect(dialog).to_have_attribute('data-content-status', 'loading')
                page.keyboard.press('Escape'); expect(dialog).to_be_hidden()
                page.goto(base+f'?date={d["date"]}&article={second["id"]}')
                expect(dialog).to_have_attribute('data-content-status', 'full')
                for route in held:
                    try: route.fulfill(json=body)
                    except Exception: pass  # An aborted stale request is expected.
                expect(page.locator('#reader-title')).to_have_text(second['title']); page.unroute(pattern)
                checks.append('late responses cannot overwrite a different article')

                page.goto(shared); expect(dialog).to_have_attribute('data-content-status', 'full')
                for w,h in [(320,740),(390,844),(768,1024),(1024,900),(1440,1000)]:
                    page.set_viewport_size({'width':w,'height':h})
                    box=dialog.bounding_box(); assert box and abs(box['width']-w)<1 and abs(box['height']-h)<1
                    assert dialog.evaluate('(d)=>d.scrollWidth<=d.clientWidth'), f'reader overflow {w}'
                    if w in (390,1440): page.screenshot(path=str(out/f'reader-{w}.png'))
                page.set_viewport_size({'width':390,'height':844})
                dialog.get_by_role('button',name='Cambia tema',exact=True).click()
                dialog.get_by_role('button',name='Cambia tema',exact=True).click()
                expect(page.locator('html')).to_have_attribute('data-theme','dark')
                page.screenshot(path=str(out/'reader-dark-390.png'))
                page.keyboard.press('Tab'); assert page.evaluate('!!document.activeElement.closest("#reader-dialog")')
                page.emulate_media(media='print'); expect(dialog).to_be_visible(); page.emulate_media(media='screen')
                checks.append('five full-screen responsive widths, dark theme, keyboard focus and print')
                assert not errors, errors
                ctx.unroute_all(behavior='wait'); ctx.close(); browser.close()
        finally:
            server.shutdown()
    assert all((news.ROOT/path).read_bytes()==raw for path,raw in production.items()), 'production data changed by reader fixtures'
    report={'result':'passed','checks':checks,'production_data_unchanged':True}
    (out/'reader-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('READER_BROWSER '+json.dumps(report,ensure_ascii=False))


if __name__ == '__main__': main()
