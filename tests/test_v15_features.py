import os
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
import re, json, subprocess, time
from playwright.sync_api import sync_playwright
srv=subprocess.Popen(['python3','-m','http.server','8770','-d',ROOT],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
time.sleep(1);errs=[]
try:
  with sync_playwright() as p:
    b=p.chromium.launch();ctx=b.new_context(viewport={'width':390,'height':780},service_workers='block')
    ctx.add_init_script("try{var s=JSON.parse(localStorage.getItem('pca_set_v1')||'{}');s.pv=false;s.lastBackup=new Date().toISOString().slice(0,10);localStorage.setItem('pca_set_v1',JSON.stringify(s));}catch(e){}")
    pg=ctx.new_page();pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:errs.append(m.text) if m.type=='error' else None)
    pg.route(re.compile(r'https://[^/]+\.workers\.dev.*'),lambda r:r.fulfill(status=200,content_type='application/json',headers={'access-control-allow-origin':'*'},body=json.dumps({'content':[{'text':'好的。'}],'stop_reason':'end_turn'})))
    pg.goto('http://localhost:8770/index.html')
    pg.fill('#pw1','pastor123');pg.fill('#pw2','pastor123');pg.check('#ack');pg.click('[data-act=setup]');pg.wait_for_selector('.sc');pg.click('.sc [data-act=close]')
    def addm(name,grp,fam,rhy='0',bd=''):
        pg.click('#tabs [data-t=flock]');pg.click('[data-act=addm]');pg.fill('#f_name',name);pg.fill('#f_grp',grp);pg.fill('#f_fam',fam);pg.select_option('#f_rhy',rhy)
        if bd:pg.fill('#f_bd',bd)
        pg.click('[data-act=savem]');pg.wait_for_selector('#flist .item')
    addm('王大明','恩典小組','王家','7','1980-12-25');addm('王小美','青年小組','王家');addm('陳志遠','恩典小組','陳家','-1')
    # grouping
    pg.select_option('#gb','fam');t=pg.inner_text('#flist');print(t.replace('\n',' | '));assert '王家（2）' in t and '陳家（1）' in t
    pg.select_option('#gb','grp');assert '恩典小組（2）' in pg.inner_text('#flist')
    # member page same-family row
    pg.click('#flist .item:has-text("王大明")');assert '王小美' in pg.inner_text('#main') and '每週' in pg.inner_text('#main');print('family row ok')
    # sensitive care + search
    pg.click('[data-act=addc]');pg.fill('#c_n','夫妻關係緊張，需要長談');pg.check('#c_s');pg.fill('#c_f','2099-01-01');pg.click('[data-act=savec]')
    pg.wait_for_selector('text=敏感紀錄（內容已隱藏）');assert '夫妻關係' not in pg.inner_text('#main');print('sens hidden ok')
    pg.click('[data-act=cshow]');assert '夫妻關係' in pg.inner_text('#main')
    pg.click('[data-act=cshow]');assert '夫妻關係' not in pg.inner_text('#main')
    pg.click('[data-act=addc]');pg.fill('#c_n','探訪時分享了詩篇23篇');pg.click('[data-act=savec]');time.sleep(.3)
    pg.click('#tabs [data-t=today]');pg.click('[data-act=search]');pg.fill('#gq','夫妻');time.sleep(.2);assert '找不到' in pg.inner_text('#gres');print('search skips sens ok')
    pg.fill('#gq','詩篇23');time.sleep(.2);assert '王大明' in pg.inner_text('#gres')
    pg.fill('#gq','恩典');time.sleep(.2);assert '王大明' in pg.inner_text('#gres') and '陳志遠' in pg.inner_text('#gres');print('search ok')
    pg.click('#gres .item >> nth=0');assert pg.locator('h1').first.inner_text()
    # rhythm: 陳志遠 -1 never quiet; 王小美 (no care, created today) not yet
    pg.click('#tabs [data-t=today]');assert '也許可以問候' not in pg.inner_text('#main');print('rhythm ok')
    # risk detection in care note
    pg.click('#tabs [data-t=flock]');pg.click('#flist .item:has-text("王小美")');pg.click('[data-act=addc]');pg.fill('#c_n','她說最近常想自殺');pg.click('[data-act=savec]')
    pg.wait_for_selector('.sc:has-text("請優先關心這位")');assert '119' in pg.inner_text('.sc');pg.click('.sc [data-act=close]')
    pg.click('#tabs [data-t=flock]');pg.click('#flist .item:has-text("王小美")');assert '敏感紀錄' in pg.inner_text('#main') and '明天' not in '' ;print('risk sheet ok')
    pg.click('[data-act=addc]');pg.fill('#c_n','先生對她家暴');pg.click('[data-act=savec]');pg.wait_for_selector('.sc:has-text("113")');pg.click('.sc [data-act=close]');print('abuse sheet ok')
    # chat crisis v2
    pg.click('#tabs [data-t=chat]');pg.click('[data-act=aion]');pg.wait_for_selector('#cin');pg.fill('#cin','有人說活著沒意思');pg.click('[data-act=send]');pg.wait_for_selector('.msg.crisis');assert '119' in pg.inner_text('.msg.crisis');print('chat crisis ok')
    pg.fill('#cin','弟兄的太太遭到家暴');pg.click('[data-act=send]');pg.wait_for_selector('.msg.crisis:has-text("113")');print('chat abuse ok')
    # ICS
    pg.click('#tabs [data-t=me]')
    pg.evaluate("window.__f=null;navigator.canShare=function(){return true};navigator.share=function(d){window.__f=d.files[0];return Promise.resolve()};0")
    pg.click('#main [data-act=ics]');pg.click('.sc [data-n="1"]');pg.wait_for_function("window.__f")
    ics=pg.evaluate("window.__f.text()");print(ics[:600]);
    assert 'BEGIN:VCALENDAR' in ics and 'RRULE:FREQ=YEARLY' in ics and '王大明' in ics and '夫妻' not in ics and '自殺' not in ics and '\r\n' in ics
    assert ics.count('BEGIN:VEVENT')==ics.count('END:VEVENT')>=3
    for line in ics.split('\r\n'): assert len(line.encode())<=75,line
    pg.evaluate("window.__f=null;0");pg.click('#main [data-act=ics]');pg.click('.sc [data-n="0"]');pg.wait_for_function("window.__f")
    ics2=pg.evaluate("window.__f.text()");assert '王大明' not in ics2 and 'RRULE' not in ics2 and '關懷跟進' in ics2;print('ics ok')
    # backup still persists after all that
    pg.reload();pg.fill('#pw','pastor123');pg.click('[data-act=unlock]');pg.wait_for_selector('.hero')
    pg.click('#tabs [data-t=flock]');assert '陳志遠' in pg.inner_text('#main')
    pg.click('#flist .item:has-text("王小美")');assert '敏感紀錄' in pg.inner_text('#main');print('persist ok')
    b.close()
finally: srv.terminate()
print('errors:',errs)
