import os
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
import re, json, subprocess, time
from playwright.sync_api import sync_playwright
srv=subprocess.Popen(['python3','-m','http.server','8774','-d',ROOT],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
time.sleep(1);errs=[];sent=[]
try:
  with sync_playwright() as p:
    b=p.chromium.launch();ctx=b.new_context(viewport={'width':390,'height':780},service_workers='block',device_scale_factor=2)
    pg=ctx.new_page();pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:errs.append(m.text) if m.type=='error' else None)
    def route(r):
        sent.append(json.loads(r.request.post_data))
        r.fulfill(status=200,content_type='application/json',headers={'access-control-allow-origin':'*'},body=json.dumps({'content':[{'text':'探訪預備：先傾聽。'}],'stop_reason':'end_turn'}))
    pg.route(re.compile(r'https://[^/]+\.workers\.dev.*'),route)
    pg.goto('http://localhost:8774/index.html')
    pg.fill('#pw1','pastor123');pg.fill('#pw2','pastor123');pg.check('#ack');pg.click('[data-act=setup]');pg.wait_for_selector('.sc');pg.click('.sc [data-act=close]')
    pg.click('#tabs [data-t=chat]');pg.click('[data-act=aion]');pg.wait_for_selector('#cin')
    assert pg.locator('.cmds [data-act=tbopen]').count()==0
    pg.click('#tabs [data-t=mini]');pg.click('#main [data-act=tbopen]');pg.wait_for_selector('.tbg')
    assert pg.locator('.tbg button').count()==7
    for x in ['探訪預備','傳福音談道預備','講章大綱','小組帶領單','代禱信／感謝信','婚禮祝福','追思致詞']:assert x in pg.inner_text('.tbg'),x
    pg.screenshot(path='/tmp/toolbox.png')
    pg.click('.tbg [data-k=visit]');pg.wait_for_selector('#tb_who')
    pg.click('[data-act=tbgo]');assert pg.locator('#tb_who').count()==1 and not sent   # empty first field blocked
    pg.fill('#tb_who','林姊妹 70歲 電話0912345678');pg.fill('#tb_sit','剛出院，心情低落')
    pg.click('[data-act=tbgo]');pg.wait_for_selector('.pv')            # preview sheet (de-id) is default on
    assert '0912345678' not in pg.inner_text('.pv') and '剛出院' in pg.inner_text('.pv')
    pg.click('[data-act=pvgo]');pg.wait_for_selector('.msg.a:has-text("先傾聽")',timeout=10000);assert pg.locator('#cin').count()==1   # jumped to chat tab
    c=sent[0]['messages'][0]['content']
    assert '預備一次牧養探訪' in c and '剛出院' in c and '0912345678' not in c,c[:200]
    assert sent[0]['model']=='claude-sonnet-5-5'
    assert '🏠 探訪預備' in pg.inner_text('.msg.u')
    # normal typed chat still works after a tool, and does not reuse the tool payload
    pg.fill('#cin','/代禱 一位家人');pg.click('[data-act=send]');pg.wait_for_selector('.pv');pg.click('[data-act=pvgo]')
    pg.wait_for_function("document.querySelectorAll('.msg.a').length>=2");assert '預備一次牧養探訪' not in sent[1]['messages'][-1]['content']
    # cancel via 回去修改 must not leak into next send
    pg.click('#tabs [data-t=mini]');pg.click('#main [data-act=tbopen]');pg.click('.tbg [data-k=wed]');pg.fill('#tb_c','小明與小美');pg.click('[data-act=tbgo]');pg.wait_for_selector('.pv');pg.click('.pv ~ .row [data-act=close], .sc .row [data-act=close]')
    pg.click('#tabs [data-t=chat]');pg.fill('#cin','你好');pg.click('[data-act=send]');pg.wait_for_selector('.pv');pg.click('[data-act=pvgo]')
    pg.wait_for_function("document.querySelectorAll('.msg.a').length>=3");assert '婚禮' not in sent[-1]['messages'][-1]['content'],sent[-1]['messages'][-1]['content']
    b.close()
finally: srv.terminate()
print('errors:',errs);assert not errs
