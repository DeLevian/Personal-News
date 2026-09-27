"""Offline DOM/layout test: fetch, local storage and history are test doubles.
Does NOT certify actual HTTP navigation, reload persistence or live images.
Optional dependency: Playwright. Set CHROMIUM_PATH for system Chromium.
"""
import json
import os
from pathlib import Path
import re
from playwright.sync_api import sync_playwright, expect
ROOT = Path(__file__).resolve().parents[1]
def main():
    data={str(p.relative_to(ROOT/'docs')):json.loads(p.read_text()) for p in (ROOT/'docs/data').rglob('*.json')}
    html=(ROOT/'docs/index.html').read_text()
    html=re.sub(r'<link[^>]*>', '', html)
    html=re.sub(r'<script[^>]*>.*?</script>', '', html)
    out=ROOT/'artifacts';out.mkdir(exist_ok=True)
    with sync_playwright() as p:
        kw={'headless':True}
        if os.environ.get('CHROMIUM_PATH'):kw['executable_path']=os.environ['CHROMIUM_PATH']
        b=p.chromium.launch(**kw)
        page=b.new_page(viewport={'width':1440,'height':1050},color_scheme='light')
        errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.set_content(html)
        page.add_style_tag(content=(ROOT/'docs/assets/styles.css').read_text()+'\n'+(ROOT/'docs/assets/media.css').read_text())
        page.evaluate('''data=>{
            const storage=new Map();
            Object.defineProperty(window,'localStorage',{value:{getItem:k=>storage.get(k)||null,setItem:(k,v)=>storage.set(k,String(v))}});
            window.fetch=async path=>({ok:path in data,status:path in data?200:404,json:async()=>data[path]});
            history.replaceState=()=>{};history.pushState=()=>{};
        }''',data)
        page.add_script_tag(content=(ROOT/'docs/assets/app.js').read_text())
        expect(page.locator('.card')).to_have_count(6)
        expect(page.locator('#prev')).to_be_enabled();expect(page.locator('#next')).to_be_disabled()
        page.locator('#search').fill('ChatGPT');expect(page.locator('.card')).to_have_count(1)
        page.locator('#reset').click();expect(page.locator('.card')).to_have_count(6)
        page.locator('#chips button').filter(has_text='Microsoft').click();expect(page.locator('.card')).to_have_count(0)
        page.locator('#empty-reset').click();expect(page.locator('.card')).to_have_count(6)
        page.locator('.save-button').first.click();page.locator('#saved').click();expect(page.locator('.card')).to_have_count(1)
        page.locator('#reset').click();page.locator('#unread').click();page.locator('.read-button').first.click();expect(page.locator('.card')).to_have_count(5)
        page.locator('#reset').click();page.locator('#scope').select_option('archive');page.locator('#search').fill('Piktiv');expect(page.locator('.card')).to_have_count(1)
        page.locator('#latest-button').click();expect(page.locator('.card')).to_have_count(6)
        page.evaluate("document.querySelectorAll('.article-image,.lead>img').forEach(i=>i.dispatchEvent(new Event('error')))")
        expect(page.locator('.article-image')).to_have_count(0)
        page.locator('#nav-archive').click();expect(page.locator('#archive-dialog')).to_be_visible();page.keyboard.press('Escape')
        page.locator('#settings-open').click();page.locator('#theme-select').select_option('dark');expect(page.locator('html')).to_have_attribute('data-theme','dark');page.locator('#theme-select').select_option('light');page.keyboard.press('Escape')
        for width,height in [(1440,1050),(1024,900),(768,1024),(390,844),(320,740)]:
            page.set_viewport_size({'width':width,'height':height})
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),f'Overflow {width}'
            if width in (1440,390):page.screenshot(path=str(out/f'preview-{width}.png'),full_page=True)
        page.set_viewport_size({'width':390,'height':844});page.locator('#mobile-archive').click();expect(page.locator('#archive-dialog')).to_be_visible();page.keyboard.press('Escape')
        assert not errors,errors
        b.close()
    result={'result':'passed','checks':['6-card initial render','two-edition boundaries','text search','category and empty state','saved filter','unread filter','archive search','return to latest','image error fallback','archive dialog','theme switching','5 responsive widths (320 to 1440)','mobile navigation','no JavaScript page errors'],'limitations':'In-memory fetch/storage/history doubles; not an HTTP end-to-end test. Live article images not loaded.'}
    (out/'dom-results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
