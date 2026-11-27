import os
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
import re, json, subprocess, time
from playwright.sync_api import sync_playwright
srv=subprocess.Popen(['python3','-m','http.server','8775','-d',ROOT],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
time.sleep(1);errs=[];sent=[]
SAMPLE='弟兄姊妹平安，今天我們來讀這段經文。主耶穌說，我是葡萄樹，你們是枝子。' * 12
try:
  with sync_playwright() as p:
    b=p.chromium.launch();ctx=b.new_context(viewport={'width':390,'height':780},service_workers='block',device_scale_factor=2)
    ctx.add_init_script("try{var s=JSON.parse(localStorage.getItem('pca_set_v1')||'{}');s.pv=false;localStorage.setItem('pca_set_v1',JSON.stringify(s));}catch(e){}")
    pg=ctx.new_page();pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:errs.append(m.text) if m.type=='error' else None)
    def route(r):
        d=json.loads(r.request.post_data);sent.append(d);c=d['messages'][0]['content'];c=c if isinstance(c,str) else c[-1]['text']
        if '風格說明' in c: t='・語氣親切口語\n・常用「弟兄姊妹平安」開場'
        elif '講章「大綱」' in c: t='# 住在主裡\n## 引言（5 分鐘）\n- 開場\n## 要點一（10 分鐘）\n- 經文\n## 結論（5 分鐘）\n- 回應'
        elif '現在只寫這一段' in c: t=re.search(r'## [^\n]+',c.split('現在只寫這一段')[1]).group(0)+'\n這是這一段的逐字稿內容。'
        elif '記憶小方法' in c: t='{"written":"","tip":"分成兩句背"}'
        else: t='小智的回答。'
        r.fulfill(status=200,content_type='application/json',headers={'access-control-allow-origin':'*'},body=json.dumps({'content':[{'text':t}],'stop_reason':'end_turn'}))
    pg.route(re.compile(r'https://[^/]+\.workers\.dev.*'),route)
    pg.goto('http://localhost:8775/index.html')
    pg.fill('#pw1','pastor123');pg.fill('#pw2','pastor123');pg.check('#ack');pg.click('[data-act=setup]');pg.wait_for_selector('.sc');pg.click('.sc [data-act=close]')
    pg.click('#tabs [data-t=chat]');pg.click('[data-act=aion]');pg.wait_for_selector('#cin')
    pg.click('#tabs [data-t=mini]');pg.click('#main [data-act=tbopen]');pg.wait_for_selector('.tbg')
    assert pg.locator('.tbg button').count()==19
    for x in ['詩歌創作','背經默寫批改','長篇講章逐字稿','我的寫作風格']:assert x in pg.inner_text('.sc'),x
    assert '睡前' not in pg.inner_text('.sc')
    pg.screenshot(path='/tmp/toolbox2.png',full_page=True)
    # song
    pg.click('.tbg [data-k=song]');pg.fill('#tb_th','詩篇 23');pg.click('[data-act=tbgo]');pg.wait_for_selector('.msg.a:has-text("小智的回答")')
    assert '原創的敬拜詩歌' in sent[-1]['messages'][0]['content']
    # style
    pg.click('#tabs [data-t=mini]');pg.click('#main [data-act=tbopen]');pg.click('[data-act=stylist]');pg.click('[data-act=stnew]')
    pg.fill('#sty_n','講台');pg.fill('#sty_s','太短');pg.click('[data-act=stmake]');assert pg.locator('#sty_s').count()==1   # too short
    pg.fill('#sty_s',SAMPLE);pg.click('[data-act=stmake]');pg.wait_for_selector('#sty_g')
    assert '語氣親切口語' in pg.input_value('#sty_g');pg.click('[data-act=stsave]');pg.wait_for_selector('.item:has-text("講台")')
    assert pg.locator('.chip:has-text("使用中")').count()==1
    pg.click('[data-act=close]')
    pg.click('#tabs [data-t=chat]');pg.fill('#cin','你好');pg.click('[data-act=send]');pg.wait_for_function("document.querySelectorAll('.msg.a').length>=2")
    assert '寫作風格' in sent[-1]['system'] and '弟兄姊妹平安' in sent[-1]['system']
    # long sermon
    n0=len(sent)
    pg.click('#tabs [data-t=mini]');pg.click('#main [data-act=tbopen]');pg.click('[data-act=lgopen]')
    pg.click('[data-act=lgout]');assert pg.locator('#lg_p').count()==1                        # needs passage
    pg.click('[data-act=gopt][data-p=lg][data-v="小組"]');pg.fill('#lg_p','約翰福音 15:1-8');pg.click('[data-act=lgmin][data-i="20"]');pg.click('[data-act=lgout]');pg.wait_for_selector('#lg_ol')
    assert '場合：小組' in sent[-1]['messages'][-1]['content'] if 'sent' in dir() else True
    assert '## 引言' in pg.input_value('#lg_ol')
    pg.click('[data-act=lgwrite]');pg.wait_for_selector('#cin',timeout=20000);pg.wait_for_selector('.msg.a:has-text("逐字稿內容")')
    assert len(sent)-n0==1+3, len(sent)-n0
    assert '住在主裡' in pg.evaluate("document.querySelector('#msgs').innerText")
    # memory verse
    pg.click('#tabs [data-t=mini]');pg.click('#main [data-act=tbopen]');pg.click('[data-act=mzopen]')
    pg.fill('#mz_r','隨便寫');pg.fill('#mz_t','x');pg.click('[data-act=mzgo]');assert pg.locator('#mz_r').count()==1
    pg.fill('#mz_r','約翰福音 3:16');pg.fill('#mz_t','神愛世人，甚至將他的獨生子賜給他們，叫一切信他的，不至滅亡，反得永生。')
    pg.click('[data-act=mzgo]');pg.wait_for_selector('.c8diff')
    t=pg.inner_text('.sc');print(t[:200]);assert '正確率' in t and '分成兩句背' in t
    assert pg.locator('.c8miss').count()>=1
    pg.click('[data-act=mzkeep]');pg.wait_for_selector('.msg.a:has-text("正確經文")')
    # persistence of style across reload
    pg.wait_for_timeout(500);pg.reload();pg.fill('#pw','pastor123');pg.click('[data-act=unlock]');pg.wait_for_selector('.hero')
    pg.click('#tabs [data-t=mini]');pg.click('#main [data-act=tbopen]');assert '使用中：講台' in pg.inner_text('.sc')
    b.close()
finally: srv.terminate()
print('errors:',errs);assert not errs
