# -*- coding: utf-8 -*-
"""교행 4-4 색인 rebuild: 직류별 섹션 구조 (교육행정 → 사서)"""
import re, json, sys, io, os
from collections import defaultdict
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('../합격선_관리_v3.html', encoding='utf-8') as f:
    html = f.read()
m = re.search(r'const RAW=(\[.*?\]);', html, re.DOTALL)
raw = json.loads(m.group(1))

# r[1]='교행', r[4]='공개경쟁', 일반, 9급만
rows = [r for r in raw
        if r[1] == '교행' and r[4] == '공개경쟁' and r[10] == '일반'
        and r[9] == '9급' and r[2] in ('2023', '2024', '2025', '2026')]

SIDO_ORDER = ['서울','부산','대구','인천','광주','대전','울산','세종',
              '경기','강원','충북','충남','전북','전남','경북','경남','제주']

# 직류별로 처리할 목록 (순서대로 섹션 생성)
JK_LIST = ['교육행정', '사서']

def fv_sel(v):
    if v in (None, ''): return '·'
    try: return str(int(round(float(str(v).replace(',', '')))))
    except: return '·'

def fv_cut(v):
    if v in (None, ''): return '·'
    try:
        f = float(str(v).replace(',', ''))
        if f > 100: f = round(f / 5, 1)  # 500점 총점 → 100점 환산
        return str(int(round(f)))
    except: return '·'

# 집계: (시도, 직류) → 연도별 (선발, 합격선)
data = defaultdict(dict)
for r in rows:
    key = (r[0], r[8].strip())
    yr = r[2]
    if yr not in data[key]:
        data[key][yr] = (r[11], r[18])

def get_jk_rows(jk):
    out = []
    for sido in SIDO_ORDER:
        key = (sido, jk)
        if key not in data: continue
        d = data[key]
        s25, c25 = d.get('2025', (None, None))
        s24, c24 = d.get('2024', (None, None))
        s23, c23 = d.get('2023', (None, None))
        yhi = fv_sel(d.get('2026', (None, None))[0])
        out.append({
            'sido': sido, 'yhi': yhi,
            'se25': fv_sel(s25), 'ct25': fv_cut(c25),
            'se24': fv_sel(s24), 'ct24': fv_cut(c24),
            'se23': fv_sel(s23), 'ct23': fv_cut(c23),
        })
    return out

# HTML 생성
COLGROUP = (
    '<colgroup>'
    '<col style="width:8mm"><col>'
    '<col><col><col><col><col><col>'
    '</colgroup>'
)
HEADER = (
    '<thead><tr>'
    '<th rowspan="2">시도</th>'
    '<th class="grp" rowspan="2">\'26<br>선</th>'
    '<th colspan="2" class="grp">\'25</th>'
    '<th colspan="2" class="grp">\'24</th>'
    '<th colspan="2" class="grp">\'23</th>'
    '</tr><tr>'
    '<th class="grp">선</th><th class="ct">컷</th>'
    '<th class="grp">선</th><th class="ct">컷</th>'
    '<th class="grp">선</th><th class="ct">컷</th>'
    '</tr></thead>'
)

def make_section(jk, rows_jk):
    jk_title = {'교육행정': '교육행정', '사서': '사서'}.get(jk, jk)
    html_rows = []
    for r in rows_jk:
        html_rows.append(
            f'<tr><td class="sd">{r["sido"]}</td>'
            f'<td class="yhi">{r["yhi"]}</td>'
            f'<td class="se">{r["se25"]}</td><td><b class="ct">{r["ct25"]}</b></td>'
            f'<td class="se">{r["se24"]}</td><td><b class="ct">{r["ct24"]}</b></td>'
            f'<td class="se">{r["se23"]}</td><td><b class="ct">{r["ct23"]}</b></td>'
            f'</tr>'
        )
    tbl = (
        f'<table class="extab fix mtx" style="font-size:6.5pt;margin-bottom:2mm">'
        f'\n{COLGROUP}\n{HEADER}\n'
        f'<tbody>\n' + '\n'.join(html_rows) + '\n</tbody>\n</table>'
    )
    return (
        f'<div style="margin-bottom:1mm">'
        f'<div style="font-size:6.5pt;font-weight:700;padding:0.8mm 0 0.4mm;'
        f'border-bottom:0.4pt solid #7da3d6;margin-bottom:0.8mm">{jk_title}</div>'
        f'{tbl}</div>'
    )

def make_spread_html(sections_html, label, show_note):
    note = (
        '<p style="margin-bottom:1.5mm;font-size:var(--fs-sm);">'
        '<b>선</b>=선발(명)·<b class="ct">컷</b>=합격선(과목평균 100점)·'
        '\'26은 선발만··=미선발</p>'
        if show_note else ''
    )
    blk = (
        f'<div class="blk fill"><div class="mh">'
        f'<span class="n mono">4-3</span>'
        f'<h3 class="serif">시·도별 합격선 색인 — {label}</h3>'
        f'<span class="flag real fb">실데이터</span></div>'
        f'<div class="bd">{note}{"".join(sections_html)}</div></div>'
    )
    folio = '<div class="folio"><span class="src">해커스공무원 필기 합격선 배치표</span><span class="pg serif">0</span></div>'
    rhead = '<div class="rhead"><span class="r">PART 4 · 지방 교육행정</span><span>시·도별 합격선 색인</span></div>'
    page = f'<div class="page">\n    {rhead}\n{blk}\n    {folio}\n  </div>'
    return f'\n  <div class="spread">{page}\n  </div>\n'

# 섹션 생성
sections = []
for jk in JK_LIST:
    jk_rows = get_jk_rows(jk)
    print(f'{jk}: {len(jk_rows)}개 시도')
    if jk_rows:
        sections.append(make_section(jk, jk_rows))

# 한 spread에 모두 넣기
spread_html = make_spread_html(sections, '교육행정·사서', show_note=True)

# 05_교행.html에서 4-4 spread 전부 제거하고 4-2 다음에 새 spread 삽입
with open('포켓북_05_교행.html', encoding='utf-8') as f:
    gyohtml = f.read()
seg = gyohtml.split('<!-- SPREADS:START -->')[1].split('<!-- SPREADS:END -->')[0]

oc = re.compile(r'<div\b[^>]*>|</div\s*>')

def extract_spread(seg, idx):
    start = seg.rfind('<div class="spread">', 0, idx)
    depth = 0; end = None
    for t in oc.finditer(seg, start):
        if t.group().startswith('</div'): depth -= 1
        else: depth += 1
        if depth == 0: end = t.end(); break
    return start, end

# 4-2 spread 끝 위치
idx42 = seg.find('"4-2"')
_, end42 = extract_spread(seg, idx42)

# 4-4 spread들 모두 찾아서 제거
pos = end42; new_seg_parts = [seg[:end42]]
remaining = seg[end42:]

# 4-4 spread들 제거
while '"4-4"' in remaining:
    idx = remaining.find('"4-4"')
    sp_start = remaining.rfind('<div class="spread">', 0, idx)
    depth = 0; sp_end = None
    for t in oc.finditer(remaining, sp_start):
        if t.group().startswith('</div'): depth -= 1
        else: depth += 1
        if depth == 0: sp_end = t.end(); break
    new_seg_parts.append(remaining[:sp_start])
    remaining = remaining[sp_end:]

new_seg_parts.append(remaining)
new_seg = (new_seg_parts[0]
           + spread_html
           + ''.join(new_seg_parts[1:]))

new_html = (
    gyohtml.split('<!-- SPREADS:START -->')[0]
    + '<!-- SPREADS:START -->'
    + new_seg
    + '<!-- SPREADS:END -->'
    + gyohtml.split('<!-- SPREADS:END -->')[1]
)

with open('포켓북_05_교행.html', 'w', encoding='utf-8') as f:
    f.write(new_html)
print('저장 완료 — 포켓북_05_교행.html')
