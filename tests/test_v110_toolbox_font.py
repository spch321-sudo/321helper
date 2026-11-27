import os
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
import subprocess, time
from playwright.sync_api import sync_playwright
srv=subprocess.Popen(['python3','-m','http.server','8778','-d',ROOT],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
time.sleep(1);errs=[]
try:
  with sync_playwright() as p:
    b=p.chromium.launch();ctx=b.new_context(viewport={'width':390,'height':780},service_workers='block')
    pg=ctx.new_page();pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto('http://localhost:8778/index.html')
    pg.fill('#pw1','pastor123');pg.fill('#pw2','pastor123');pg.check('#ack');pg.click('[data-act=setup]');pg.wait_for_selector('.sc');pg.click('.sc [data-act=close]')
    pg.click('#tabs [data-t=mini]');pg.click('#main [data-act=tbopen]');pg.wait_for_selector('.tbg')
    fs=lambda sel:pg.evaluate("parseFloat(getComputedStyle(document.querySelector('%s')).fontSize)"%sel)
    for cls,base in [('',16),('fs1',18),('fs3',22)]:
        pg.evaluate("document.documentElement.className='%s'"%cls)
        t,d=fs('.tbg b'),fs('.tbg small');print(cls,t,d)
        assert t==base and d<t and abs(d-base*.85)<.1
    b.close()
finally: srv.terminate()
print('errors:',errs);assert not errs
