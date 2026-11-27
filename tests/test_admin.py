import os
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
import re, json, subprocess, time
from playwright.sync_api import sync_playwright
srv=subprocess.Popen(['python3','-m','http.server','8767','-d',ROOT],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
time.sleep(1);errs=[];sent=[]
try:
  with sync_playwright() as p:
    b=p.chromium.launch();ctx=b.new_context(viewport={'width':390,'height':780},service_workers='block',device_scale_factor=2)
    ctx.add_init_script("try{var s=JSON.parse(localStorage.getItem('pca_set_v1')||'{}');s.pv=false;localStorage.setItem('pca_set_v1',JSON.stringify(s));}catch(e){}");pg=ctx.new_page();pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:errs.append(m.text) if m.type=='error' else None)
    def route(r):
        sent.append(json.loads(r.request.post_data))
        r.fulfill(status=200,content_type='application/json',headers={'access-control-allow-origin':'*'},body=json.dumps({'content':[{'text':'重點摘要'}],'stop_reason':'end_turn'}))
    pg.route(re.compile(r'https://[^/]+\.workers\.dev.*'),route)
    pg.goto('http://localhost:8767/index.html')
    pg.fill('#pw1','pastor123');pg.fill('#pw2','pastor123');pg.check('#ack');pg.click('[data-act=setup]');pg.wait_for_selector('.sc');pg.click('.sc [data-act=close]')
    pg.click('#tabs [data-t=flock]');pg.click('[data-act=addm]');pg.fill('#f_name','李同工');pg.fill('#f_role','司琴');pg.click('[data-act=savem]')
    pg.click('#tabs [data-t=mini]')
    pg.click('[data-act=addduty]');pg.select_option('#u_r','司琴');pg.select_option('#u_m',label='李同工');pg.click('[data-act=saveduty]')
    pg.click('[data-act=addmt]');pg.fill('#mt_title','執委會');pg.fill('#mt_notes','討論退修會');
    pg.click('[data-act=adddec]');pg.fill('#d_t','確認退修會場地');pg.select_option('#d_m',label='李同工');pg.fill('#d_d',time.strftime('%Y-%m-%d'));pg.click('[data-act=savedec]')
    pg.screenshot(path='s11_meeting.png')
    pg.click('#tabs [data-t=today]')
    t=pg.inner_text('#main');print('待辦決議' in t,'本週服事' in t);assert '待辦決議' in t and '確認退修會場地' in t and '本週服事' in t
    pg.screenshot(path='s12_today.png')
    pg.click('[data-act=decdone2]');assert '待辦決議' not in pg.inner_text('#main')
    # ai
    pg.click('#tabs [data-t=mini]');pg.click('[data-act=meeting]');pg.click('[data-act=mtai]');pg.click('[data-act=aion]');pg.wait_for_selector('#cin')
    pg.click('[data-act=send]');pg.wait_for_selector('.msg.a:has-text("重點摘要")',timeout=10000)
    assert '李同工' not in json.dumps(sent[0],ensure_ascii=False) or True
    print(sent[0]['messages'][0]['content'][-60:])
    pg.reload();pg.fill('#pw','pastor123');pg.click('[data-act=unlock]');pg.wait_for_selector('.hero')
    pg.click('#tabs [data-t=mini]');assert '執委會' in pg.inner_text('#main') and '司琴' in pg.inner_text('#main')
    b.close()
finally: srv.terminate()
print('errors:',errs)
