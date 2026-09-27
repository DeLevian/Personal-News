"""Verify the actual deployed Pages app and every configured article image.
Read-only network checks. No tokens, private sources, or asset copying into repo.
"""
import hashlib,json,os,time,urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
def read(url):
    req=urllib.request.Request(url,headers={'User-Agent':'PersonalNewsDeploymentCheck/1.0'})
    with urllib.request.urlopen(req,timeout=20) as r:return r.read(4000000)
def main():
    cfg=json.loads((ROOT/'config/pipeline.json').read_text())
    base=cfg.get('website_url')
    if not base:
        print('LIVE_RESULT '+json.dumps({'result':'not-configured'}));return
    manifest=json.loads((ROOT/'docs/data/index.json').read_text())
    expected=(ROOT/'docs/assets/app.js').read_bytes()
    latest=manifest['editions'][0]
    ready=False
    candidates=[base.rstrip('/')+'/',base.rstrip('/')+'/docs/']
    for attempt in range(36):
        for candidate in dict.fromkeys(candidates):
            try:
                live=json.loads(read(candidate+'data/index.json?check='+str(time.time_ns())))
                js=read(candidate+'assets/app.js?check='+str(time.time_ns()))
                if live['updated_at']==manifest['updated_at'] and hashlib.sha256(js).digest()==hashlib.sha256(expected).digest():
                    edition_bytes_match=all(hashlib.sha256(read(candidate+entry['path']+'?check='+str(time.time_ns()))).digest()==hashlib.sha256((ROOT/'docs'/entry['path']).read_bytes()).digest() for entry in manifest['editions'][:2])
                    asset_bytes_match=all(hashlib.sha256(read(candidate+name+'?check='+str(time.time_ns()))).digest()==hashlib.sha256((ROOT/'docs'/name).read_bytes()).digest() for name in ['index.html','assets/v2.css'])
                    if edition_bytes_match and asset_bytes_match:
                        base=candidate;ready=True;break
            except Exception as e:print('WAITING_DEPLOY',candidate,str(e),flush=True)
        if ready:break
        time.sleep(5)
    if not ready:raise AssertionError('Pages has not yet published the tested data/code after waiting for propagation')
    out=ROOT/'artifacts';out.mkdir(exist_ok=True)
    report={'result':'running','entry_url':cfg['website_url'],'url':base,'edition':manifest['latest'],'images':[],'widths':[]}
    with sync_playwright() as p:
        options={'headless':True}
        if os.environ.get('CHROMIUM_PATH'):options['executable_path']=os.environ['CHROMIUM_PATH']
        browser=p.chromium.launch(**options)
        context=browser.new_context(viewport={'width':1440,'height':1050},color_scheme='light')
        page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(cfg['website_url'],wait_until='domcontentloaded')
        expect(page).to_have_url(base)
        report['public_entry_redirect']='passed'
        for entry in manifest['editions'][:2]:
            data=json.loads((ROOT/'docs'/entry['path']).read_text())
            target=base+'?date='+entry.get('id',entry['date'])
            page.goto(target,wait_until='domcontentloaded')
            expect(page.locator('.card')).to_have_count(len(data['items']))
            for item in data['items']:
                if not item.get('image'):continue
                card=page.locator('[id="'+item['id']+'"]');card.scroll_into_view_if_needed()
                try:
                    expect(card.locator('.article-image')).to_be_visible(timeout=12000)
                    page.wait_for_function("id=>{const i=document.getElementById(id)?.querySelector('.article-image');return !!(i&&i.complete&&i.naturalWidth>0)}",arg=item['id'],timeout=12000)
                    dim=card.locator('.article-image').evaluate('(i)=>({width:i.naturalWidth,height:i.naturalHeight,src:i.currentSrc})')
                    report['images'].append({'id':item['id'],'ok':True,**dim})
                except Exception as e:report['images'].append({'id':item['id'],'ok':False,'url':item['image']['url'],'error':str(e)[:350]})
        page.goto(base,wait_until='domcontentloaded');expect(page.locator('.card')).to_have_count(latest['count'])
        current=json.loads((ROOT/'docs'/latest['path']).read_text())
        attention=current.get('attention_today');now=datetime.now(ZoneInfo('Europe/Rome'))
        active=bool(attention and current['date']==now.date().isoformat() and datetime.fromisoformat(attention['valid_from'])<=now<datetime.fromisoformat(attention['expires_at']))
        if active:
            expect(page.locator('#attention-today')).to_be_visible()
            expect(page.locator('#attention-today')).to_contain_text('DA SAPERE OGGI')
        elif current['date']==now.date().isoformat():
            expect(page.locator('#attention-today')).to_be_hidden()
        report['attention_current_state']='passed'
        for card in page.locator('.card').all():card.scroll_into_view_if_needed()
        page.wait_for_timeout(700)
        for width,height in [(1440,1050),(1024,900),(768,1024),(390,844),(320,740)]:
            page.set_viewport_size({'width':width,'height':height})
            page.evaluate("window.scrollTo({top:0,left:0,behavior:'instant'})")
            page.wait_for_function('window.scrollY===0')
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),f'Overflow at {width}'
            report['widths'].append(width)
            if width in (1440,390):
                page.screenshot(path=str(out/f'live-{width}.png'),full_page=True)
                page.screenshot(path=str(out/f'viewport-{width}.png'),full_page=False)
        page.set_viewport_size({'width':390,'height':844})
        if latest['count'] and page.locator('.image-expand').count():
            page.locator('.image-expand').first.click();expect(page.locator('#image-dialog')).to_be_visible()
            page.wait_for_function('document.getElementById("full-image").naturalWidth>0')
            page.keyboard.press('Escape');expect(page.locator('#image-dialog')).not_to_be_visible()
            report['image_lightbox']='passed'
        counts=latest.get('counts',{'main':latest['count'],'radar':0})
        page.locator('[data-section-filter=radar]').click();expect(page.locator('.card')).to_have_count(counts['radar'])
        page.locator('[data-section-filter=main]').click();expect(page.locator('.card')).to_have_count(counts['main'])
        page.locator('[data-section-filter=all]').click();expect(page.locator('.card')).to_have_count(latest['count'])
        report['section_filters']='passed';report['counts']=counts
        toggle=page.locator('#mobile-chrome-toggle');expect(toggle).to_be_visible();expect(page.locator('.topbar')).to_be_hidden();expect(page.locator('#mobile-nav')).to_be_hidden()
        toggle.click();expect(page.locator('.topbar')).to_be_visible();expect(page.locator('#mobile-nav')).to_be_visible()
        page.locator('#mobile-archive').click();expect(page.locator('#archive-dialog')).to_be_visible();expect(toggle).to_have_attribute('aria-expanded','false');page.keyboard.press('Escape')
        toggle.click()
        if len(manifest['editions'])>1:
            page.locator('#prev').click();expect(page.locator('#next')).to_be_enabled()
        page.locator('#latest-button').click();expect(page.locator('.card')).to_have_count(latest['count'])
        report['mobile_reading_chrome']='passed';report['live_navigation']='passed';report['javascript_errors']=errors
        browser.close()
    report['result']='passed' if not errors and all(i['ok'] for i in report['images']) else 'failed'
    (out/'live-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('LIVE_RESULT '+json.dumps(report,ensure_ascii=False))
    if report['result']!='passed':raise AssertionError('Live browser/image checks failed; inspect live-results.json')
if __name__=='__main__':main()
