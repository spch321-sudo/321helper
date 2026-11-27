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
    pg.click('#tabs [data-t=app]');t=pg.text_content('#main')
    for x in ['晨讀321','321互動聖經','321生命操練','321健康新生活','國度321空中團契','Kimi','ChatGPT','DeepSeek','Claude','豆包','Gemini','不要貼上會友的姓名']:assert x in t,x
    hrefs=pg.eval_on_selector_all('a.appc','els=>els.map(e=>e.href)')
    assert 'https://spch321-sudo.github.io/bible/' in hrefs and 'https://claude.ai/' in hrefs and len(hrefs)==23,len(hrefs)
    assert pg.eval_on_selector_all('a.appc','els=>els.every(e=>e.target=="_blank"&&e.rel.indexOf("noopener")>=0)')
    assert pg.locator('.chip.cn').count()==3
    pg.screenshot(path='/tmp/app_tab.png')
    # clicking a card must not break the app (stays unlocked)
    with ctx.expect_page() as np:
        pg.click('a.appc >> nth=3')
    np.value.close();assert pg.locator('#tabs').is_visible()
    b.close()
finally: srv.terminate()
print('errors:',errs)
