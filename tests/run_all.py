# 執行全部自動化測試：python3 tests/run_all.py   （需要 playwright 與 chromium）
import os,subprocess,sys,glob
d=os.path.dirname(os.path.abspath(__file__));bad=[]
for f in sorted(glob.glob(os.path.join(d,'test_*.py'))):
    r=subprocess.run([sys.executable,f],capture_output=True,text=True,timeout=300)
    ok=r.returncode==0 and 'errors: []' in r.stdout
    print(('PASS ' if ok else 'FAIL ')+os.path.basename(f))
    if not ok:bad.append(f);print(r.stdout[-800:],r.stderr[-800:])
sys.exit(1 if bad else 0)
