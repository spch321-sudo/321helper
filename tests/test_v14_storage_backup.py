import os
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
import re, json, subprocess, time
from playwright.sync_api import sync_playwright
srv=subprocess.Popen(['python3','-m','http.server','8767','-d',ROOT],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
time.sleep(1);errs=[];sent=[]
URL='http://localhost:8767/index.html'
def idb_vault(pg):
    return pg.evaluate("""()=>new Promise(r=>{var q=indexedDB.open('pca_db',1);q.onsuccess=()=>{try{var g=q.result.transaction('kv').objectStore('kv').get('pca_vault_v1');g.onsuccess=()=>r(g.result||null);}catch(e){r('ERR')}};q.onerror=()=>r('ERR');})""")
try:
  with sync_playwright() as p:
    b=p.chromium.launch()
    # ---- A: new vault -> IDB, 600000
    ctx=b.new_context(viewport={'width':390,'height':780},service_workers='block')
    pg=ctx.new_page();pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:errs.append(m.text) if m.type=='error' else None)
    def route(r):
        sent.append(json.loads(r.request.post_data))
        r.fulfill(status=200,content_type='application/json',headers={'access-control-allow-origin':'*'},body=json.dumps({'content':[{'text':'平安。'}],'stop_reason':'end_turn'}))
    pg.route(re.compile(r'https://[^/]+\.workers\.dev.*'),route)
    pg.goto(URL)
    pg.fill('#pw1','pastor123');pg.fill('#pw2','pastor123');pg.check('#ack');pg.click('[data-act=setup]');pg.wait_for_selector('.sc');pg.click('.sc [data-act=close]')
    time.sleep(1.5)
    v=json.loads(idb_vault(pg));print('A it=',v.get('it'),'v=',v.get('v'));assert v['it']==600000 and v['v']==2
    assert pg.evaluate("localStorage.getItem('pca_vault_v1')") is None
    # add member
    pg.click('#tabs [data-t=flock]');pg.click('[data-act=addm]')
    pg.fill('#f_name','王大明');pg.fill('#f_nick','大明')
    pg.click('[data-act=savem]');pg.wait_for_selector('#flist .item')
    # reminder card (members exist, never backed up)
    pg.click('#tabs [data-t=today]');assert '還沒有備份過' in pg.inner_text('#main');print('A reminder ok')
    # share backup
    pg.evaluate("window.__sh=0;navigator.canShare=function(){return true};navigator.share=function(d){window.__sh=d.files[0].name;return Promise.resolve()};0")
    pg.click('#main [data-act=export]');pg.wait_for_function("window.__sh")
    print('A share file:',pg.evaluate("window.__sh"));assert pg.evaluate("window.__sh").startswith('pca-backup-')
    pg.wait_for_function("!document.body.innerText.includes('還沒有備份過')");print('A reminder cleared')
    # preview: send with member name and phone
    pg.click('#tabs [data-t=chat]');pg.click('[data-act=aion]');pg.wait_for_selector('#cin')
    pg.fill('#cin','王大明最近很疲憊，電話0912345678，住在新竹市東區光復路二段101號');pg.click('[data-act=send]')
    pg.wait_for_selector('.pv');pv=pg.inner_text('.pv');print('A preview:',pv)
    assert '王大明' not in pv and '會友甲' in pv and '0912345678' not in pv and '光復路' not in pv
    assert len(sent)==0
    pg.click('[data-act=pvgo]');pg.wait_for_selector('.msg.a:has-text("平安")',timeout=10000)
    c=sent[0]['messages'][0]['content'];assert '王大明' not in c and '會友甲' in c;print('A sent ok')
    # verse check v2 : ai text with quote
    # ---- lock/unlock persistence
    pg.reload();pg.fill('#pw','pastor123');pg.click('[data-act=unlock]');pg.wait_for_selector('.hero')
    pg.click('#tabs [data-t=flock]');assert '王大明' in pg.inner_text('#main');print('A reload ok')
    ctx.close()
    # ---- B: legacy localStorage vault (150000) migrates and upgrades
    ctx=b.new_context(viewport={'width':390,'height':780},service_workers='block')
    pg=ctx.new_page();pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:errs.append(m.text) if m.type=='error' else None)
    pg.goto(URL)
    pg.evaluate("""async()=>{var enc=new TextEncoder(),salt=crypto.getRandomValues(new Uint8Array(16)),iv=crypto.getRandomValues(new Uint8Array(12));
      var k0=await crypto.subtle.importKey('raw',enc.encode('oldpass1'),'PBKDF2',false,['deriveKey']);
      var k=await crypto.subtle.deriveKey({name:'PBKDF2',salt:salt,iterations:150000,hash:'SHA-256'},k0,{name:'AES-GCM',length:256},false,['encrypt']);
      var d={v:1,members:[{id:'m1',name:'李小華',nick:'',cat:'',grp:'',role:'',bd:'',ph:'',nt:'',created:'2026-01-01'}],cares:[],prayers:[],days:{},chat:[],sermons:[],meetings:[],duties:[],set:{pname:'老牧'}};
      var ct=await crypto.subtle.encrypt({name:'AES-GCM',iv:iv},k,enc.encode(JSON.stringify(d)));
      function b2s(a){a=new Uint8Array(a);var s='';for(var i=0;i<a.length;i++)s+=String.fromCharCode(a[i]);return btoa(s);}
      localStorage.setItem('pca_vault_v1',JSON.stringify({v:1,salt:b2s(salt),iv:b2s(iv),ct:b2s(ct)}));}""")
    pg.reload();pg.fill('#pw','oldpass1');pg.click('[data-act=unlock]');pg.wait_for_selector('.hero');assert '老牧' in pg.inner_text('.hero')
    time.sleep(4)
    v=json.loads(idb_vault(pg));print('B it=',v.get('it'));assert v['it']==600000
    assert pg.evaluate("localStorage.getItem('pca_vault_v1')") is None
    pg.reload();pg.fill('#pw','oldpass1');pg.click('[data-act=unlock]');pg.wait_for_selector('.hero');print('B relock after upgrade ok')
    pg.click('#tabs [data-t=flock]');assert '李小華' in pg.inner_text('#main')
    # wrong password
    pg.evaluate("document.querySelector('[data-act=lock]')&&0")
    # change password path
    pg.click('#tabs [data-t=me]');pg.click('[data-act=chpw]');pg.fill('#o_pw','oldpass1');pg.fill('#n_pw','newpass22');pg.fill('#n_pw2','newpass22');pg.click('[data-act=dochpw]');time.sleep(2)
    pg.reload();pg.fill('#pw','newpass22');pg.click('[data-act=unlock]');pg.wait_for_selector('.hero');print('B chpw ok')
    ctx.close();b.close()
finally: srv.terminate()
print('errors:',errs)
