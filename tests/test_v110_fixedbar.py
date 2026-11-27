import os
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
import re, json, subprocess, time
from playwright.sync_api import sync_playwright
srv=subprocess.Popen(['python3','-m','http.server','8777','-d',ROOT],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
time.sleep(1);errs=[]
try:
  with sync_playwright() as p:
    b=p.chromium.launch();ctx=b.new_context(viewport={'width':390,'height':780},service_workers='block',device_scale_factor=2)
    ctx.add_init_script("try{var s=JSON.parse(localStorage.getItem('pca_set_v1')||'{}');s.pv=false;localStorage.setItem('pca_set_v1',JSON.stringify(s));}catch(e){}")
    pg=ctx.new_page();pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route(re.compile(r'https://[^/]+\.workers\.dev.*'),lambda r:r.fulfill(status=200,content_type='application/json',headers={'access-control-allow-origin':'*'},body=json.dumps({'content':[{'text':'很長的回答。'*120}],'stop_reason':'end_turn'})))
    pg.goto('http://localhost:8777/index.html')
    pg.fill('#pw1','pastor123');pg.fill('#pw2','pastor123');pg.check('#ack');pg.click('[data-act=setup]');pg.wait_for_selector('.sc');pg.click('.sc [data-act=close]')
    pg.click('#tabs [data-t=chat]');pg.click('[data-act=aion]');pg.wait_for_selector('#cin')
    for i in range(4):
        pg.fill('#cin','問題%d'%i);pg.click('[data-act=send]');pg.wait_for_function("document.querySelectorAll('.msg.a').length>=%d"%(i+1))
    def gap():
        return pg.evaluate("(function(){var t=document.getElementById('tabs').getBoundingClientRect().top,c=document.querySelector('.cbar').getBoundingClientRect();return Math.round(t-c.bottom);})()")
    print('gap at bottom',gap());assert abs(gap())<=2
    pg.evaluate("document.getElementById('main').scrollTop=0");print('gap at top',gap());assert abs(gap())<=2
    pg.evaluate("document.getElementById('main').scrollTop=1500");assert abs(gap())<=2
    pg.click('#tabs [data-t=today]');assert pg.evaluate("document.getElementById('main').style.paddingBottom")==''
    b.close()
finally: srv.terminate()
print('errors:',errs);assert not errs
