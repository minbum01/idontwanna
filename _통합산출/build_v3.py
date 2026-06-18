# -*- coding: utf-8 -*-
"""합격선_관리_v3 = v2(검증본 2023~2025 + 국가직 2026) + 추가분(2026 지방직 접수현황) 병합.

두 HTML(합격선_관리_v2.html / 합격선_관리_추가분.html)이 동일한 RAW 형식(같은 KMAP)이라
RAW(데이터)·DONE(확인파일)·LINKS(파일링크)를 추출해 합쳐 v3를 만든다. (원본 CSV 불필요)
"""
import os, json

D = os.path.dirname(os.path.abspath(__file__))
V2  = os.path.join(D, "합격선_관리_v2.html")
ADD = os.path.join(D, "합격선_관리_추가분.html")
OUT = os.path.join(D, "합격선_관리_v3.html")

def slice_between(html, start_marker, end_marker):
    i = html.index(start_marker) + len(start_marker)
    j = html.index(end_marker, i)
    return html[i:j]

def extract(html):
    raw  = slice_between(html, "const RAW=",  ";\nconst DB=")
    done = slice_between(html, "const DONE=", ",TOTAL=")
    links= slice_between(html, ",LINKS=",     ",ISSUES=")
    return json.loads(raw), json.loads(done), json.loads(links)

v2_html  = open(V2,  encoding="utf-8").read()
add_html = open(ADD, encoding="utf-8").read()

raw_v2, done_v2, links_v2 = extract(v2_html)
raw_add, done_add, links_add = extract(add_html)

# ── 병합 (완전 동일 행은 중복 제거) ──
seen, merged = set(), []
for r in raw_v2 + raw_add:
    key = tuple(r)
    if key in seen:
        continue
    seen.add(key)
    merged.append(r)

done  = sorted(set(done_v2) | set(done_add))
links = {**links_v2, **links_add}

# ── v2 템플릿에 병합 데이터 갈아끼우기 ──
raw_v2_str  = slice_between(v2_html, "const RAW=",  ";\nconst DB=")
done_v2_str = slice_between(v2_html, "const DONE=", ",TOTAL=")
links_v2_str= slice_between(v2_html, ",LINKS=",     ",ISSUES=")

out = v2_html
out = out.replace("const RAW="  + raw_v2_str,  "const RAW="  + json.dumps(merged, ensure_ascii=False, separators=(',', ':')), 1)
out = out.replace("const DONE=" + done_v2_str, "const DONE=" + json.dumps(done,  ensure_ascii=False), 1)
out = out.replace(",LINKS="     + links_v2_str, ",LINKS="     + json.dumps(links, ensure_ascii=False), 1)

# 제목/헤더 v3 표기
out = out.replace("<title>합격선 관리 v2 (검증본)</title>",
                  "<title>합격선 관리 v3 (검증본 + 2026 접수)</title>")
out = out.replace("<h1>✅ 합격선 관리 v2 — 검증본</h1>",
                  "<h1>✅ 합격선 관리 v3 — 검증본 + 2026 접수현황</h1>")

open(OUT, "w", encoding="utf-8").write(out)

def y(rows):
    from collections import Counter
    return dict(Counter(r[2] for r in rows))  # 연도 = index 2

print(f"v3 생성: {OUT}")
print(f"  v2 행 {len(raw_v2):,} + 추가분 {len(raw_add):,} → 병합 {len(merged):,} (중복 {len(raw_v2)+len(raw_add)-len(merged)} 제거)")
print(f"  v2 연도분포 : {y(raw_v2)}")
print(f"  추가분 연도 : {y(raw_add)}")
print(f"  병합 연도   : {y(merged)}")
print(f"  확인파일 {len(done):,} · 파일링크 {len(links):,}")
