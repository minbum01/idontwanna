# -*- coding: utf-8 -*-
"""전체 파이프라인 한 번에 실행(순서 고정). 접수enrich는 merge 뒤에 와야 함."""
import subprocess, sys, os
D=os.path.dirname(__file__)
STEPS=[
 "parse_seoul.py","parse_busan_hwp.py","parse_busan_pdf.py","parse_daegu.py",
 "parse_incheon.py","parse_gwangju.py","parse_gyeonggi.py","parse_ulsan.py",
 "parse_municipal.py","parse_gwangju_gyo.py","parse_gyo_new.py",
 "build_gyohaeng.py","build_gyo_extra.py",
 "enrich_eungsi.py",      # 교행 응시현황(소스 CSV 수정)
 "merge.py",              # 통합
 "enrich_jeopsu.py",      # 접수현황 → 병합파일에 접수 채움(merge 뒤!)
 "build_xlsx.py","build_status_md.py","build_html.py",
]
for s in STEPS:
    print("▶",s); r=subprocess.run([sys.executable,os.path.join(D,s)],capture_output=True,text=True,encoding="utf-8")
    out=(r.stdout or "").strip().splitlines()
    if out: print("  ",out[-1])
    if r.returncode!=0: print("  ERR:",(r.stderr or "")[-300:])
print("완료")
