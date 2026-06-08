# -*- coding: utf-8 -*-
"""지역별 파싱 CSV들을 합격선_통합_v2.csv로 병합."""
import csv, os
D=os.path.dirname(__file__)
SOURCES=["합격선_통합.csv","부산_공무원_hwp.csv","부산_공무원_pdf.csv","대구_공무원.csv","인천_공무원.csv","광주_대전_공무원.csv","경기.csv","울산_공무원.csv","신규4_공무원.csv","교행_data.csv","광주_교행.csv","교행_신규pdf.csv","교행_추가.csv"]
hdr=None; allrows=[]
for f in SOURCES:
    p=os.path.join(D,f)
    if not os.path.exists(p):
        print("WARN 없음:",f); continue
    with open(p,encoding="utf-8-sig") as fp:
        r=list(csv.reader(fp))
    if hdr is None: hdr=r[0]
    allrows+=r[1:]
with open(os.path.join(D,"합격선_통합_merged.csv"),"w",encoding="utf-8-sig",newline="") as fp:
    w=csv.writer(fp); w.writerow(hdr); w.writerows(allrows)
from collections import Counter
print("merged:",len(allrows), dict(Counter((x[0],x[1]) for x in allrows)))
