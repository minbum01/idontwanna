# -*- coding: utf-8 -*-
import subprocess, os, time, fitz
D=os.path.dirname(__file__)
CHROME=r"C:\Program Files\Google\Chrome\Application\chrome.exe"
r=subprocess.run(["py",os.path.join(D,"_gen_gukga7.py")],capture_output=True,text=True)
print(r.stdout,(r.stderr[-600:] if r.stderr else ""))
src="file:///"+os.path.join(D,"포켓북_03_국가직7급.html").replace("\\","/")
pdf=os.path.join(D,"_tmp_r7.pdf")
subprocess.run([CHROME,"--headless=new","--disable-gpu","--no-pdf-header-footer","--virtual-time-budget=15000","--run-all-compositor-stages-before-draw","--print-to-pdf="+pdf,src],capture_output=True,timeout=120)
time.sleep(1)
doc=fitz.open(pdf)
print("g7 standalone pages:",doc.page_count)
for i in range(doc.page_count):
    doc[i].get_pixmap(matrix=fitz.Matrix(1.85,1.85)).save(os.path.join(D,f"_tmp_r7_{i+1}.png"))
print("ok")
