import os
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
import subprocess, time
from playwright.sync_api import sync_playwright
srv=subprocess.Popen(['python3','-m','http.server','8773','-d',ROOT],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
time.sleep(1);errs=[]
try:
  with sync_playwright() as p:
    b=p.chromium.launch();ctx=b.new_context(viewport={'width':390,'height':780},service_workers='block',device_scale_factor=2)
    pg=ctx.new_page();pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:errs.append(m.text) if m.type=='error' else None)
    pg.goto('http://localhost:8773/index.html')
    pg.fill('#pw1','pastor123');pg.fill('#pw2','pastor123');pg.check('#ack');pg.click('[data-act=setup]');pg.wait_for_selector('.sc');pg.click('.sc [data-act=close]')
    assert pg.locator('#tabs button').count()==6
    pg.click('#tabs [data-t=app]')
    vis=lambda:pg.locator('a.appc:visible').count()
    assert vis()==2+2+2+1,vis()
    tx=pg.inner_text('#main')
    for x in ['展開其它 4 個','展開其它 2 個','展開其它 6 個','展開全部 6 個']:assert x in tx,x
    assert '中國可用' not in pg.text_content('#main')
    pg.screenshot(path='/tmp/app_tab.png')
    while pg.locator('details.appfold:not([open])').count():pg.click('details.appfold:not([open]) > summary >> nth=0')
    assert vis()==6+4+8+1+6,vis()
    assert pg.locator('details.appfold[open]').count()==4
    # state persists after re-render (tab switch) and in localStorage
    pg.click('#tabs [data-t=app]');assert pg.locator('details.appfold[open]').count()==4
    assert '"ai":1' in pg.evaluate("localStorage.getItem('pca_appfold')")
    t=pg.text_content('#main')
    for x in ['晨讀321','321互動聖經','321心靈快餐','321真理點心','321生命操練','321健康新生活','國度321空中團契','Kimi','ChatGPT','DeepSeek','Claude','豆包','Gemini','不要貼上會友的姓名']:assert x in t,x
    hrefs=pg.eval_on_selector_all('a.appc','els=>els.map(e=>e.href)')
    for u in ['bible/','321soul/','321truth/','321fellowship/']:assert 'https://spch321-sudo.github.io/'+u in hrefs,u
    assert 'https://claude.ai/' in hrefs and len(hrefs)==25,len(hrefs)
    assert pg.eval_on_selector_all('a.appc','els=>els.every(e=>e.target=="_blank"&&e.rel.indexOf("noopener")>=0)')
    pg.click('details.appfold[open] > summary >> nth=0');assert vis()<len(hrefs)
    pg.evaluate('window.scrollTo(0,0)')
    # clicking a card must not break the app (stays unlocked)
    with ctx.expect_page() as np:
        pg.click('a.appc >> nth=1')
    np.value.close();assert pg.locator('#tabs').is_visible()
    b.close()
finally: srv.terminate()
print('errors:',errs)
