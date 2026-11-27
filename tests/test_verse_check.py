import os
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
import re, json, subprocess, time
from playwright.sync_api import sync_playwright
srv=subprocess.Popen(['python3','-m','http.server','8768','-d',ROOT],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
time.sleep(1);errs=[]
try:
  with sync_playwright() as p:
    b=p.chromium.launch();ctx=b.new_context(viewport={'width':390,'height':780},service_workers='block')
    ctx.add_init_script("try{var s=JSON.parse(localStorage.getItem('pca_set_v1')||'{}');s.pv=false;localStorage.setItem('pca_set_v1',JSON.stringify(s));}catch(e){}")
    pg=ctx.new_page();pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:errs.append(m.text) if m.type=='error' else None)
    txt='「耶和華是我的牧者，我必不致缺乏。」（詩 23:1）又說「神愛世人，甚至將他獨生子賜給他們」（約翰福音 3:16），也可讀腓4:6-7 與 弗 2:8。'
    pg.route(re.compile(r'https://[^/]+\.workers\.dev.*'),lambda r:r.fulfill(status=200,content_type='application/json',headers={'access-control-allow-origin':'*'},body=json.dumps({'content':[{'text':txt}],'stop_reason':'end_turn'})))
    pg.goto('http://localhost:8768/index.html')
    pg.fill('#pw1','pastor123');pg.fill('#pw2','pastor123');pg.check('#ack');pg.click('[data-act=setup]');pg.wait_for_selector('.sc');pg.click('.sc [data-act=close]')
    pg.click('#tabs [data-t=chat]');pg.click('[data-act=aion]');pg.wait_for_selector('#cin');pg.fill('#cin','/經文 憂慮');pg.click('[data-act=send]')
    pg.wait_for_selector('.msg.a:has-text("牧者")',timeout=10000)
    pg.wait_for_function("document.querySelectorAll('.vv').length>=3");time.sleep(.5)
    t=pg.evaluate("document.querySelector('.ver').textContent");print(t)
    assert '詩篇 23:1' in t and '約翰福音 3:16' in t and '弗' not in t.replace('以弗所書','')
    assert '以弗所書 2:8' in t
    assert t.count('✓ 小智的引文與和合本相符')==1 and t.count('字句與和合本不同')==1
    assert '腓' not in t  # ambiguous abbreviation not parsed
    b.close()
finally: srv.terminate()
print('errors:',errs)
