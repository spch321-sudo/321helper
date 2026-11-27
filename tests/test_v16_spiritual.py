import os
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
import re, json, subprocess, time
from playwright.sync_api import sync_playwright
srv=subprocess.Popen(['python3','-m','http.server','8772','-d',ROOT],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
time.sleep(1);errs=[]
try:
  with sync_playwright() as p:
    b=p.chromium.launch();ctx=b.new_context(viewport={'width':390,'height':780},service_workers='block')
    ctx.add_init_script("try{var s=JSON.parse(localStorage.getItem('pca_set_v1')||'{}');s.pv=false;s.lastBackup=new Date().toISOString().slice(0,10);localStorage.setItem('pca_set_v1',JSON.stringify(s));}catch(e){}")
    pg=ctx.new_page();pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:errs.append(m.text) if m.type=='error' else None)
    sent=[]
    def route(r):
        sent.append(json.loads(r.request.post_data));r.fulfill(status=200,content_type='application/json',headers={'access-control-allow-origin':'*'},body=json.dumps({'content':[{'text':'好的。'}],'stop_reason':'end_turn'}))
    pg.route(re.compile(r'https://[^/]+\.workers\.dev.*'),route)
    pg.goto('http://localhost:8772/index.html')
    pg.fill('#pw1','pastor123');pg.fill('#pw2','pastor123');pg.check('#ack');pg.click('[data-act=setup]');pg.wait_for_selector('.sc');pg.click('.sc [data-act=close]')
    # four sections in order
    t=pg.inner_text('#main');idx=[t.index(x) for x in ['與主','與己','與人','與事']];assert idx==sorted(idx);print('sections order ok')
    assert '務要牧養在你們中間神的群羊' in t and '彼得前書 5:2-3' in t
    # exam saves
    pg.fill('#ex0','我想要被肯定');pg.fill('#ex1','聚會後的關懷');pg.fill('#ex2','一切歸給主');pg.click('#main h1')  # blur
    time.sleep(.3);pg.click('[data-act=exhist]');tt=pg.inner_text('.sc');assert '我想要被肯定' in tt and '一切歸給主' in tt;pg.click('.sc [data-act=close]');print('exam ok')
    # sabbath + burnout
    pg.check('[data-act=sab]');pg.click('[data-act=bo]');
    for i in (0,1,3):pg.check('#bo%d'%i)
    pg.click('[data-act=bosave]');pg.wait_for_selector('.sc:has-text("不是診斷")');pg.click('.sc [data-act=close]');print('burnout ok')
    # members
    def addm(n,extra=None):
        pg.click('#tabs [data-t=flock]');pg.click('[data-act=addm]');pg.fill('#f_name',n)
        if extra:extra()
        pg.click('[data-act=savem]');pg.wait_for_selector('#flist .item')
    addm('張三');addm('李四');addm('王五');addm('趙六')
    # 235 consent rule
    pg.click('#flist .item:has-text("李四")');pg.click('[data-act=editm]');pg.select_option('#f_235','屬靈戰友');pg.click('[data-act=savem]');time.sleep(.3)
    assert '屬靈戰友' not in pg.inner_text('#main');print('235 no consent -> not saved')
    pg.click('[data-act=editm]');pg.select_option('#f_235','屬靈戰友');pg.check('#f_235c');pg.click('[data-act=savem]');time.sleep(.3)
    assert '屬靈戰友' in pg.inner_text('#main');print('235 with consent ok')
    # visit pre + post lines
    assert '求你在這次相遇中作王' in pg.inner_text('#main')
    pg.click('[data-act=addc]');pg.fill('#c_n','拜訪家中');pg.click('.sc summary');pg.fill('#c_r1','他很孤單');pg.fill('#c_r2','我先聽不急著講');pg.fill('#c_r3','下週打電話');pg.click('[data-act=savec]');time.sleep(.3)
    mt=pg.inner_text('#main');assert '看見：他很孤單' in mt and '放下：我先聽不急著講' in mt;print('post-visit lines ok')
    pg.click('#tabs [data-t=today]');pg.click('[data-act=search]');pg.fill('#gq','不急著講');time.sleep(.3);assert '李四' in pg.inner_text('#gres');print('search r ok')
    # prayer wheel (4 members -> 3 per day)
    pg.click('#tabs [data-t=today]');assert pg.locator('[data-act=pwheel]').count()==3
    pg.check('[data-act=pwheel] >> nth=0');print('wheel ok')
    # peer
    pg.click('[data-act=peerset]');pg.select_option('#pe_m',label='王五');pg.click('[data-act=peersave]');tt=pg.inner_text('#main');assert '屬靈同伴：王五' in tt and '超過兩週' in tt
    pg.click('[data-act=peerdone]');assert '超過兩週' not in pg.inner_text('#main');print('peer ok')
    # persistence
    time.sleep(1.5);pg.reload();pg.fill('#pw','pastor123');pg.click('[data-act=unlock]');pg.wait_for_selector('.hero')
    assert pg.input_value('#ex0')=='我想要被肯定' and pg.is_checked('[data-act=sab]') and '屬靈同伴：王五' in pg.inner_text('#main');print('persist ok')
    # toggle off hides
    pg.click('#tabs [data-t=me]');pg.click('[data-act=sotog]');pg.click('#tabs [data-t=today]');t=pg.inner_text('#main');assert '與己' not in t and '無己省察' not in t;print('toggle off ok')
    # edit question
    pg.click('#tabs [data-t=me]');pg.click('[data-act=sotog]');pg.click('summary:has-text("自訂語句")');pg.fill('#s_q0','我今天哪裡想作王？');pg.press('#s_q0','Tab')
    pg.click('#tabs [data-t=today]');assert '我今天哪裡想作王？' in pg.inner_text('#main');print('custom question ok')
    # AI boundary in system prompt
    pg.click('#tabs [data-t=chat]');pg.click('[data-act=aion]');pg.wait_for_selector('#cin');pg.fill('#cin','你好');pg.click('[data-act=send]');pg.wait_for_selector('.msg.a:has-text("好的")')
    sy=sent[0]['system'];assert '不替聖靈說話' in sy and '321理念只在牧養與勸勉類' in sy;print('sys boundary ok')
    b.close()
finally: srv.terminate()
print('errors:',errs)
