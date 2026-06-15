# -*- coding: utf-8 -*-
import csv, os, io
from collections import defaultdict
D=os.path.dirname(__file__)
rows=list(csv.DictReader(open(os.path.join(D,"검증_data.csv"),encoding="utf-8-sig")))
g7=[r for r in rows if r["지역"]=="국가직" and r["직급"]=="7급"]
def num(s):
    s=(s or "").replace(",","").strip()
    try:return float(s)
    except:return 0
out=io.StringIO()
out.write("g7 rows: %d\n"%len(g7))
out.write("회차 종류: %s\n"%sorted(set(r['회차'] for r in g7)))
out.write("연도: %s\n"%sorted(set(r['연도'] for r in g7)))
out.write("대상: %s\n"%dict((d,sum(1 for r in g7 if r['대상']==d)) for d in sorted(set(r['대상'] for r in g7))))
# 연도×회차 합계
out.write("\n=== 연도×회차 합계(선발/출원/응시/필기합격) ===\n")
for y in ["2023","2024","2025"]:
    for hc in ["1차-PSAT","2차-전공"]:
        rs=[r for r in g7 if r['연도']==y and r['회차']==hc]
        sb=sum(num(r['선발예정인원']) for r in rs);cw=sum(num(r['접수인원']) for r in rs)
        eu=sum(num(r['응시인원']) for r in rs);hp=sum(num(r['필기합격인원']) for r in rs)
        out.write(f"{y} {hc}: 선발 {int(sb)} 출원 {int(cw)} 응시 {int(eu)} 합격 {int(hp)} (행 {len(rs)})\n")
# 직류 목록 (2차-전공, 일반, 2025)
out.write("\n=== 2025 2차-전공 일반 직류 (직렬/직류/선발/출원/응시/합격선/양성/비고) ===\n")
for r in g7:
    if r['연도']=='2025' and r['회차']=='2차-전공' and r['대상']=='일반':
        out.write(f'{r["직렬"]}/{r["직류"]} 선{r["선발예정인원"]} 출{r["접수인원"]} 응{r["응시인원"]} 합{r["합격선"]} 양{r["양성평등합격선"]} {r["비고"]}\n')
out.write("\n=== 2025 1차-PSAT 일반 직류 (합격선=PSAT) 샘플 ===\n")
for r in g7:
    if r['연도']=='2025' and r['회차']=='1차-PSAT' and r['대상']=='일반':
        out.write(f'{r["직렬"]}/{r["직류"]} 선{r["선발예정인원"]} 응{r["응시인원"]} 합{r["합격선"]}\n')
open(os.path.join(D,"_tmp_an7.txt"),"w",encoding="utf-8").write(out.getvalue())
print("done", len(g7))
