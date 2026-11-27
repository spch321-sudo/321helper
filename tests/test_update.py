import os
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
import subprocess,time,shutil,tempfile,json
from playwright.sync_api import sync_playwright
tmp=tempfile.mkdtemp();
for f in os.listdir(ROOT):
    if f in('tests','bible','.git'):continue
    if os.path.isfile(os.path.join(ROOT,f)):shutil.copy(os.path.join(ROOT,f),tmp)
json.dump({'version':'9.9.9'},open(os.path.join(tmp,'version.json'),'w'))
srv=subprocess.Popen(['python3','-m','http.server','8771','-d',tmp],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
errs=[];navs=[]
try:
  with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_context(viewport={'width':390,'height':780},service_workers='block').new_page()
    pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('framenavigated',lambda f:navs.append(f.url) if f==pg.main_frame else None)
    pg.goto('http://localhost:8771/index.html')
    last=-1;t0=time.time()
    while time.time()-t0<20:
        time.sleep(2)
        if len(navs)==last and pg.locator('#pw1').count():break
        last=len(navs)
    print('navigations',len(navs));assert 2<=len(navs)<=3   # one auto-update reload, then loop guard stops it
    pg.wait_for_selector('#pw1');pg.wait_for_function("!document.getElementById('updbar').hidden",timeout=10000);print('update bar shown after guard')
    b.close()
finally:
    srv.terminate();shutil.rmtree(tmp,ignore_errors=True)
print('errors:',errs);assert not errs
