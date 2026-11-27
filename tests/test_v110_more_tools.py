import json, os
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
import re, json, subprocess, time
from playwright.sync_api import sync_playwright
srv=subprocess.Popen(['python3','-m','http.server','8776','-d',ROOT],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
time.sleep(1);errs=[];sent=[]
HTML='<!DOCTYPE html><html><head><meta charset="utf-8"><title>奉獻加總</title></head><body><input id="a" type="number"><button onclick="document.getElementById(\'r\').textContent=Number(document.getElementById(\'a\').value)*2">算</button><div id="r"></div></body></html>'
try:
  with sync_playwright() as p:
    b=p.chromium.launch();ctx=b.new_context(viewport={'width':390,'height':780},service_workers='block',device_scale_factor=2,accept_downloads=True)
    ctx.add_init_script("try{var s=JSON.parse(localStorage.getItem('pca_set_v1')||'{}');s.pv=false;localStorage.setItem('pca_set_v1',JSON.stringify(s));}catch(e){}")
    pg=ctx.new_page();pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:errs.append(m.text) if m.type=='error' else None)
    def route(r):
        d=json.loads(r.request.post_data);sent.append(d);c=d['messages'][0]['content'];c=c if isinstance(c,str) else c[-1]['text']
        st='end_turn'
        if '請做這個小工具' in c or '請依下面的要求修改' in c: t=HTML
        elif '投影片' in c and 'JSON' in c: t=json.dumps({'title':'住在主裡','subtitle':'約翰福音 15','slides':[{'t':'主旨','p':['住在主裡','結果子']},{'t':'經文','p':[],'v':'我是葡萄樹','r':'約翰福音 15:5'},{'t':'禱告','p':['求主幫助我們']}]})
        elif '祝福的話' in c or '卡片祝福' in c: t='願主賜福你，阿們'
        else: t='小智的回答。'
        r.fulfill(status=200,content_type='application/json',headers={'access-control-allow-origin':'*'},body=json.dumps({'content':[{'text':t}],'stop_reason':st}))
    pg.route(re.compile(r'https://[^/]+\.workers\.dev.*'),route)
    PNG=open('/tmp/ph.png','rb').read()
    def pxr(r):
        if 'api.pexels.com' in r.request.url:
            r.fulfill(status=200,headers={'access-control-allow-origin':'*','content-type':'application/json'},body=json.dumps({"photos":[{"photographer":"Tester","src":{"tiny":"https://images.pexels.com/t.png","large2x":"https://images.pexels.com/l.png"}}]}))
        else: r.fulfill(status=200,headers={'access-control-allow-origin':'*','content-type':'image/png'},body=PNG)
    BG={"cats":[{"id":"bible","n":"聖經故事"},{"id":"cats","n":"貓咪"},{"id":"cakes","n":"蛋糕"}],"list":[{"f":"a.jpg","t":"as.jpg","c":"bible","n":"伊甸園"},{"f":"b.jpg","t":"bs.jpg","c":"cats","n":"小貓"}]}
    def bgr(r):
        if r.request.url.endswith('bg.json'): r.fulfill(status=200,headers={'access-control-allow-origin':'*','content-type':'application/json'},body=json.dumps(BG))
        else: r.fulfill(status=200,headers={'access-control-allow-origin':'*','content-type':'image/png'},body=PNG)
    pg.route(re.compile(r'https://spch321-sudo\.github\.io/bible/.*'),bgr)
    pg.route(re.compile(r'https://(api|images)\.pexels\.com/.*'),pxr)
    pg.goto('http://localhost:8776/index.html')
    pg.fill('#pw1','pastor123');pg.fill('#pw2','pastor123');pg.check('#ack');pg.click('[data-act=setup]');pg.wait_for_selector('.sc');pg.click('.sc [data-act=close]')
    pg.click('#tabs [data-t=chat]');pg.click('[data-act=aion]');pg.wait_for_selector('#cin')
    def box():
        if pg.locator('#sheet.show').count(): pg.click('#sheet [data-act=close]')
        pg.click('#tabs [data-t=mini]');pg.click('#main [data-act=tbopen]');pg.wait_for_selector('.tbg')
    box();assert pg.locator('.tbg button').count()==19,pg.locator('.tbg button').count()
    for x in ['編寫週報','寫牧養短文','寫靈修小品','事工計劃表','財務報表','製作投影片','製作卡片','做成小工具','設計提示詞']:assert x in pg.inner_text('.sc'),x
    pg.screenshot(path='/tmp/toolbox3.png',full_page=True)
    # text tools reach the model with their spec
    for k,first,marker in [('week','items','教會週報'),('pshort','topic','牧養短文'),('devo','t','靈修小品'),('plan','m','事工計劃表'),('fin','per','收支報表'),('prm','need','提示詞')]:
        pg.click('.tbg [data-k=%s]'%k);pg.fill('#tb_%s'%first,'測試內容 0912345678');pg.click('[data-act=tbgo]')
        pg.wait_for_selector('#cin');pg.wait_for_function("document.querySelectorAll('.msg.a').length>=%d"%(['week','pshort','devo','plan','fin','prm'].index(k)+1))
        c=sent[-1]['messages'][-1]['content'];assert marker in c and '0912345678' not in c,(k,c[:80])
        if k=='prm': sy=sent[-1]['system']+sent[-1]['messages'][-1]['content'] if isinstance(sent[-1]['messages'][-1]['content'],str) else sent[-1]['system'];assert '提示詞開始' in sy and '不需要引用經文' in sy and '完整引用經文' not in sy
        box()
    # guided options: multi-select chips, chips-only send
    pg.click('.sc [data-act=close]');pg.click('#tabs [data-t=mini]');assert pg.evaluate("document.querySelector('#main .card .item').getAttribute('data-act')")=='tbopen'
    pg.click('#main [data-act=tbopen]');pg.click('.tbg [data-k=visit]')
    assert pg.locator('.tbog').count()==3
    pg.click('.tbog [data-v="住院病患"]');pg.click('.tbog [data-v="長者"]');pg.click('.tbog [data-v="一起禱告"]');pg.click('.tbog [data-v="長者"]')
    pg.click('[data-act=tbgo]');pg.wait_for_selector('#cin');pg.wait_for_function("document.querySelectorAll('.msg.a').length>=7")
    c=sent[-1]['messages'][-1]['content'];assert '對象：住院病患' in c and '長者' not in c.split('這次的目的')[0] and '一起禱告' in c,c[:200]
    box()
    # mini tool
    box();pg.click('[data-act=mtopen]');pg.click('[data-act=mtgo]');assert pg.locator('#mt_q').count()==1
    pg.click('[data-act=mtchip] >> nth=0');assert pg.input_value('#mt_q')
    pg.click('[data-act=mtgo]');pg.wait_for_selector('#mtfr',timeout=20000)
    fr=pg.frame_locator('#mtfr');fr.locator('#a').fill('21');fr.locator('button').click();assert fr.locator('#r').inner_text()=='42'
    with pg.expect_download() as dl: pg.click('[data-act=mtdl]')
    assert dl.value.suggested_filename.endswith('.html')
    pg.click('[data-act=mtsave]');pg.wait_for_selector('.item:has-text("奉獻加總")')
    pg.click('[data-act=mtbig]');pg.wait_for_selector('#mtbig iframe');pg.click('[data-act=mtbigx]');assert pg.locator('#mtbig').count()==0
    pg.fill('#mt_m','字大一點');pg.click('[data-act=mtmod]');pg.wait_for_selector('#mtfr')
    assert '請依下面的要求修改' in sent[-1]['messages'][0]['content']
    pg.click('[data-act=mtnew]');pg.click('[data-act=mtload]');pg.wait_for_selector('#mtfr')
    # slides
    box();pg.click('[data-act=slopen]');pg.click('[data-act=slgo]');assert pg.locator('#sl_s').count()==1
    pg.fill('#sl_s','約翰福音 15 葡萄樹的講章');pg.click('[data-act=slmine]');pg.fill('#sl_s','約翰福音 15 葡萄樹的講章');pg.click('[data-act=slgo]')
    pg.wait_for_selector('[data-act=sldl]',timeout=30000)
    with pg.expect_download() as d2: pg.click('[data-act=sldl]')
    f=d2.value;assert f.suggested_filename.endswith('.pptx');path=f.path();import zipfile
    z=zipfile.ZipFile(path);assert any(n.startswith('ppt/slides/slide') for n in z.namelist()) and len([n for n in z.namelist() if re.match(r'ppt/slides/slide\d+\.xml',n)])==4
    # card
    box();pg.click('[data-act=cdopen]');pg.wait_for_selector('#cdcv');pg.fill('#cd_to','林姊妹');pg.fill('#cd_tx','生日快樂，主祝福你。')
    pg.click('[data-act=cdtpl][data-k="rose"]');assert pg.input_value('#cd_to')=='林姊妹'
    assert pg.locator('[data-act=cdtpl]').count()==9 and pg.locator('[data-act=cdbd]').count()==6 and pg.locator('[data-act=cdsize]').count()==4 and pg.locator('[data-act=cdfs]').count()==5
    pg.click('[data-act=cdsize][data-k="p"]');assert pg.evaluate("[document.getElementById('cdcv').width,document.getElementById('cdcv').height]")==[1080,1920]
    pg.click('[data-act=cdsize][data-k="w"]');assert pg.evaluate("document.getElementById('cdcv').width")==1920
    pg.click('[data-act=cdbd][data-k="ornate"]');pg.click('[data-act=cdfs][data-k="1.45"]');pg.click('[data-act=cdsize][data-k="t"]')
    pg.fill('#cd_v','願耶和華賜福給你，保護你。');pg.fill('#cd_vs','民數記 6:24')
    pg.set_input_files('#cd_file','/tmp/ph.png');pg.wait_for_selector('[data-act=cdnophoto]')
    assert pg.input_value('#cd_v')=='願耶和華賜福給你，保護你。'
    pg.click('[data-act=cdgal]');pg.wait_for_selector('[data-act=cdgpick]')
    assert pg.locator('[data-act=cdgcat]').count()==2
    pg.click('[data-act=cdgcat][data-k="cats"]');assert pg.locator('[data-act=cdgpick]').count()==1
    pg.click('[data-act=cdgpick]');pg.wait_for_selector('[data-act=cdnophoto]');pg.click('[data-act=cdnophoto]')
    pg.click('[data-act=cdpx]');pg.wait_for_selector('[data-act=cdpxpick]');pg.click('[data-act=cdpxpick]');pg.wait_for_selector('[data-act=cdnophoto]')
    pg.click('[data-act=cdimp]');pg.click('[data-act=cdimp2][data-k="更溫暖"]');pg.wait_for_function("document.getElementById('cd_tx').value.indexOf('願主賜福')>=0")
    pg.fill('#cd_tx','生日快樂，主祝福你。')
    pg.click('[data-act=cdwrite]');pg.wait_for_function("document.getElementById('cd_tx').value.indexOf('願主賜福')>=0")
    pg.screenshot(path='/tmp/card.png')
    with pg.expect_download() as d3: pg.click('[data-act=cddl]')
    assert d3.value.suggested_filename.endswith('.png')
    b.close()
finally: srv.terminate()
errs=[e for e in errs if 'serviceWorker' not in e]  # emitted by the test harness inside sandboxed iframes
print('errors:',errs);assert not errs
