# -*- coding: utf-8 -*-
"""지역×(공무원/교행) 취합현황을 O/△/X로 MD 생성."""
import openpyxl, os, re
from collections import Counter
base=r"C:/Users/admin/Documents/이민범 개발/합격선/합격선 최종모음"
OUT=r"C:/Users/admin/Documents/이민범 개발/합격선/_통합산출/취합현황.md"
DATE="2026-06-08"
EXT={'.pdf','.hwp','.hwpx','.xlsx','.xls','.png'}
wb=openpyxl.load_workbook(os.path.join(os.path.dirname(OUT),"합격선_통합.xlsx"))
H=[c.value for c in wb['합격선통합'][1]]; I={h:i for i,h in enumerate(H)}
cnt=Counter(); used=set()
for s in ['합격선통합','합격선_경력경쟁']:
    for r in wb[s].iter_rows(min_row=2,values_only=True):
        cnt[(r[I['지역']],r[I['시험종류']])]+=1; used.add(r[I['원본파일명']])

def is_hap(fn):
    if os.path.splitext(fn)[1].lower() not in EXT: return False
    if any(k in fn for k in ('접수','응시','현황','출원','경쟁률','명단','원서')): return False
    return any(k in fn for k in ('합격선','합격자','붙임2','합격'))

folders={}
for d in os.listdir(base):
    p=os.path.join(base,d)
    if os.path.isdir(p):
        m=re.match(r'\d+\s*(\S+)\s*(공무원|교행)',d)
        if m: folders[(m.group(1),m.group(2))]=os.listdir(p)

order=['서울','부산','대구','인천','광주','대전','울산','경기','강원','충북','충남','전북','전남','경북','경남','제주','세종']
def st(reg,kind):
    rows=cnt.get((reg,kind),0)
    fs=folders.get((reg,kind),[])
    hap=[f for f in fs if is_hap(f)]
    left=[f for f in hap if f not in used and '2026' not in f]
    if rows>0 and not left: return 'O',rows,0
    if rows>0 and left: return '△',rows,len(left)
    if rows==0 and hap: return 'X',0,len(left)   # 파일 있으나 미처리
    return '—',0,0                                 # 데이터 없음

g=Counter(); h=Counter(); lines=[]; detail=[]
for reg in order:
    gs,gn,gl=st(reg,'공무원'); hs,hn,hl=st(reg,'교행')
    g[gs]+=1; h[hs]+=1
    lines.append(f"| {reg} | {gs} | {hs} |")
    if gs in('△','X'): detail.append(f"- **{reg} 공무원** {gs} — 처리 {gn}행, 미처리 합격선 파일 {gl}개")
    if hs in('△','X'): detail.append(f"- **{reg} 교행** {hs} — 처리 {hn}행, 미처리 합격선 파일 {hl}개")

md=f"""# 📋 합격선 데이터 취합 현황

> 기준일: {DATE} · 자동 산출(파싱 결과 + 미반영 파일 대조)

**범례**  O 완료 · △ 부분(일부 연도/파일만) · X 미착수(파일 있으나 미처리) · — 데이터 없음

| 지역 | 공무원 | 교행 |
|:----:|:------:|:----:|
""" + "\n".join(lines) + f"""

## 요약
- **공무원**: O {g['O']} · △ {g['△']} · X {g['X']} · — {g['—']}
- **교행**: O {h['O']} · △ {h['△']} · X {h['X']} · — {h['—']}
- 합격선 데이터: {sum(cnt.values()):,}행 ({len([1 for k in cnt if k[1]=='공무원'])}개 공무원 / {len([1 for k in cnt if k[1]=='교행'])}개 교행 지역)

## △·X 상세 (남은 작업)
""" + "\n".join(detail) + "\n"

open(OUT,"w",encoding="utf-8").write(md)
print("생성:",OUT)
print(md)
