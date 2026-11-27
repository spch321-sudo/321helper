import os
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
import re, json, subprocess, time
from playwright.sync_api import sync_playwright
srv=subprocess.Popen(['python3','-m','http.server','8766','-d',ROOT],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
time.sleep(1);errs=[];sent=[]
try:
  with sync_playwright() as p:
    b=p.chromium.launch();ctx=b.new_context(viewport={'width':390,'height':780},service_workers='block',device_scale_factor=2)
    ctx.add_init_script("try{var s=JSON.parse(localStorage.getItem('pca_set_v1')||'{}');s.pv=false;localStorage.setItem('pca_set_v1',JSON.stringify(s));}catch(e){}");pg=ctx.new_page();pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:errs.append(m.text) if m.type=='error' else None)
    def route(r):
        sent.append(json.loads(r.request.post_data))
        r.fulfill(status=200,content_type='application/json',headers={'access-control-allow-origin':'*'},body=json.dumps({'content':[{'text':'優點：脈絡清楚。'}],'stop_reason':'end_turn'}))
    pg.route(re.compile(r'https://[^/]+\.workers\.dev.*'),route)
    pg.goto('http://localhost:8766/index.html')
    pg.fill('#pw1','pastor123');pg.fill('#pw2','pastor123');pg.check('#ack');pg.click('[data-act=setup]');pg.wait_for_selector('.sc');pg.click('.sc [data-act=close]')
    pg.click('#tabs [data-t=mini]');pg.click('[data-act=addsm]')
    pg.fill('#sv_title','愛的次序');pg.fill('#sv_ref','約翰福音 3:16-17');pg.fill('#sv_theme','神愛世人');pg.fill('#sv_points','一、神愛\n二、子賜');
    pg.click('[data-act=slook]');pg.wait_for_selector('#spass .vv');t=pg.inner_text('#spass');print(t[:120]);assert '神愛世人' in t and '3'.strip()
    pg.click('[data-act=sstage][data-k="0"]')
    pg.screenshot(path='s10_sermon.png')
    pg.click('[data-act=sreview]');pg.wait_for_selector('[data-act=aion]');pg.click('[data-act=aion]');pg.wait_for_selector('#cin')
    assert '神愛' in pg.input_value('#cin')
    pg.click('[data-act=send]');pg.wait_for_selector('.msg.a:has-text("脈絡清楚")',timeout=10000)
    print(sent[0]['model'],sent[0]['messages'][0]['content'][:30])
    assert sent[0]['model']=='claude-sonnet-5-5'
    pg.fill('#cin','/勸慰 一位家人剛過世');pg.click('[data-act=send]');pg.wait_for_function("document.querySelectorAll('.msg.a').length>=2")
    assert sent[1]['model']=='claude-haiku-5-5'
    assert pg.locator('.cmds button').count()==11
    # persistence
    pg.reload();pg.fill('#pw','pastor123');pg.click('[data-act=unlock]');pg.wait_for_selector('.hero')
    pg.click('#tabs [data-t=mini]');assert '愛的次序' in pg.inner_text('#main')
    pg.click('.item[data-act=sermon]');assert pg.input_value('#sv_theme')=='神愛世人';assert pg.is_checked('[data-k="0"]')
    b.close()
finally: srv.terminate()
print('errors:',errs)
