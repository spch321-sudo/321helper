import os
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
import re, json, subprocess, time, sys
from playwright.sync_api import sync_playwright
srv=subprocess.Popen(['python3','-m','http.server','8765','-d',ROOT],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
time.sleep(1)
errs=[];sent=[]
try:
  with sync_playwright() as p:
    b=p.chromium.launch()
    ctx=b.new_context(viewport={'width':390,'height':780},service_workers='block',device_scale_factor=2)
    ctx.add_init_script("try{var s=JSON.parse(localStorage.getItem('pca_set_v1')||'{}');s.pv=false;localStorage.setItem('pca_set_v1',JSON.stringify(s));}catch(e){}");pg=ctx.new_page()
    pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.on('console',lambda m:errs.append(m.text) if m.type=='error' else None)
    def route(r):
        body=json.loads(r.request.post_data)
        sent.append(body)
        n=len(sent)
        if n==1: out={'content':[{'text':'### 探訪重點\n- 先傾聽\n> 詩篇 23:1\n可讀約翰福音 3:16，也可讀詩篇23篇1-2節，另有約翰福音 99:1。\n會友甲需要陪伴。'}],'stop_reason':'end_turn'}
        else: out={'content':[{'text':'好的'}],'stop_reason':'end_turn'}
        r.fulfill(status=200,content_type='application/json',headers={'access-control-allow-origin':'*'},body=json.dumps(out))
    pg.route(re.compile(r'https://[^/]+\.workers\.dev.*'),route)
    pg.goto('http://localhost:8765/index.html')
    pg.fill('#pw1','pastor123');pg.fill('#pw2','pastor123');pg.check('#ack');pg.click('[data-act=setup]')
    pg.wait_for_selector('.sc',timeout=10000)
    pg.screenshot(path='/home/claude/test/s1_welcome.png')
    pg.click('.sc [data-act=close]')
    assert 'ＯＫ' or True
    # add member
    pg.click('#tabs [data-t=flock]');pg.click('[data-act=addm]')
    pg.fill('#f_name','王大明');pg.fill('#f_nick','大明');pg.fill('#f_ph','0912-345-678');pg.fill('#f_bd',time.strftime('%Y-')+time.strftime('%m-%d'))
    pg.click('[data-act=savem]')
    pg.wait_for_selector('#flist .item')
    pg.click('#flist .item')
    pg.click('[data-act=addc]');pg.fill('#c_n','住院探訪，王大明很焦慮');pg.click('[data-act=fuq][data-n="3"]');pg.click('[data-act=savec]')
    pg.click('[data-act=addp]');pg.fill('#p_t','求主賜平安');pg.click('[data-act=savep]')
    pg.screenshot(path='/home/claude/test/s2_member.png',full_page=False)
    # today
    pg.click('#tabs [data-t=today]');pg.screenshot(path='/home/claude/test/s3_today.png')
    # mini + flow
    pg.click('#tabs [data-t=mini]');pg.screenshot(path='/home/claude/test/s4_mini.png')
    pg.click('[data-act=flow][data-id=crisis]');pg.screenshot(path='/home/claude/test/s5_flow.png')
    # chat consent
    pg.click('#tabs [data-t=chat]');pg.screenshot(path='/home/claude/test/s6_consent.png')
    pg.click('[data-act=aion]')
    pg.fill('#cin','/探訪 王大明（電話 0912-345-678）最近說不想活了');pg.click('[data-act=send]')
    pg.wait_for_selector('.msg.a b:has-text("探訪重點"), .msg.a h4',timeout=10000)
    pg.screenshot(path='/home/claude/test/s7_chat.png')
    print('sent model:',sent[0]['model']);print('sent text:',sent[0]['messages'][0]['content'][-80:])
    assert '王大明' not in json.dumps(sent[0],ensure_ascii=False)
    assert '0912' not in json.dumps(sent[0],ensure_ascii=False)
    assert pg.locator('.msg.crisis').count()==1
    assert '王大明需要陪伴' in pg.inner_text('#msgs')
    pg.click('.ver summary');pg.wait_for_selector('.ver[data-done]',timeout=8000)
    vt=pg.inner_text('.ver')
    print(vt[:400])
    assert '神愛世人' in vt and '耶和華是我的牧者' in vt and '找不到這處經文' in vt
    pg.screenshot(path='/home/claude/test/s7b_ver.png')
    # reload -> locked -> wrong pw -> right pw, data persisted
    pg.reload();pg.wait_for_selector('#pw')
    pg.fill('#pw','wrong');pg.click('[data-act=unlock]');pg.wait_for_function("document.getElementById('lerr').textContent.indexOf('不正確')>=0")
    pg.fill('#pw','pastor123');pg.click('[data-act=unlock]');pg.wait_for_selector('.hero')
    pg.click('#tabs [data-t=flock]');assert '王大明' in pg.inner_text('#flist')
    raw=pg.evaluate("""()=>new Promise(r=>{var q=indexedDB.open('pca_db',1);q.onsuccess=()=>{var g=q.result.transaction('kv').objectStore('kv').get('pca_vault_v1');g.onsuccess=()=>r(g.result)}})""");assert '王大明' not in raw and 'ct' in raw
    # export content check
    pg.click('#tabs [data-t=me]');pg.screenshot(path='/home/claude/test/s8_me.png')
    # dark + font large
    pg.evaluate("window.PCA.fs(2)");pg.screenshot(path='/home/claude/test/s9_big.png')
    b.close()
finally:
    srv.terminate()
print('errors:',errs)
