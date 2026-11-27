import os
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
import subprocess,time,shutil,tempfile,json,re
from playwright.sync_api import sync_playwright
tmp=tempfile.mkdtemp()
for f in os.listdir(ROOT):
    if f in('tests','bible','.git'):continue
    if os.path.isfile(os.path.join(ROOT,f)):shutil.copy(os.path.join(ROOT,f),tmp)
cur=re.search(r"APPVER='([^']+)'",open(os.path.join(ROOT,'index.html'),encoding='utf8').read()).group(1)
json.dump({'version':cur},open(os.path.join(tmp,'version.json'),'w'))
srv=subprocess.Popen(['python3','-m','http.server','8780','-d',tmp],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
errs=[];navs=[]
try:
  with sync_playwright() as p:
    b=p.chromium.launch();ctx=b.new_context(viewport={'width':390,'height':780},service_workers='block')
    ctx.add_init_script("window.PCA_UPPOLL=800;window.PCA_UPIDLE=1500;window.PCA_UPTICK=400;")
    pg=ctx.new_page();pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('framenavigated',lambda f:navs.append(f.url) if f==pg.main_frame else None)
    pg.goto('http://localhost:8780/index.html')
    pg.fill('#pw1','pastor123');pg.fill('#pw2','pastor123');pg.check('#ack');pg.click('[data-act=setup]');pg.wait_for_selector('.sc');pg.click('.sc [data-act=close]')
    n0=len(navs)
    json.dump({'version':'9.9.9'},open(os.path.join(tmp,'version.json'),'w'))
    # user is typing -> must NOT reload
    pg.click('#tabs [data-t=me]');pg.wait_for_selector('#s_pn');pg.focus('#s_pn');pg.keyboard.type('X')
    pg.wait_for_timeout(4000);assert len(navs)==n0,'reloaded while typing'
    pg.wait_for_function("!document.getElementById('updbar').hidden")
    # stop typing, leave focus -> auto update after idle
    pg.evaluate("document.activeElement.blur()")
    t0=time.time()
    while time.time()-t0<12 and len(navs)==n0:pg.wait_for_timeout(300)
    assert len(navs)>n0,'no auto update when idle'
    pg.wait_for_selector('#pw1,#pw');pg.wait_for_timeout(3000);print('navs after update',len(navs)-n0);assert len(navs)-n0<=2
    b.close()
finally:
    srv.terminate();shutil.rmtree(tmp,ignore_errors=True)
print('errors:',errs);assert not errs
