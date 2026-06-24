# -*- coding: utf-8 -*-
"""교행 직류별 시·도별 합격선 색인 rebuild
   직류별 spread 1개씩: 4-3 교육행정 / 4-4 사서 / 4-5 전산 / 4-6 건축
"""
import re, json, sys, io, os
from collections import defaultdict
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('../합격선_관리_v3.html', encoding='utf-8') as f:
    html = f.read()
m = re.search(r'const RAW=(\[.*?\]);', html, re.DOTALL)
raw = json.loads(m.group(1))

rows = [r for r in raw
        if r[1] == '교행' and r[4] == '공개경쟁' and r[10] == '일반'
        and r[9] == '9급' and r[2] in ('2023', '2024', '2025', '2026')]

SIDO_ORDER = ['서울','부산','대구','인천','광주','대전','울산','세종',
              '경기','강원','충북','충남','전북','전남','경북','경남','제주']

# 직류 → (섹션번호, 헤더 라벨)
JK_CONFIG = [
    ('교육행정', '4-3', '교육행정'),
    ('사서',     '4-4', '사서'),
    ('전산',     '4-5', '전산'),
    ('건축',     '4-6', '건축'),
]

def fv_sel(v):
    if v in (None, ''): return '·'
    try: return str(int(round(float(str(v).replace(',', '')))))
    except: return '·'

def fv_cut(v):
    if v in (None, ''): return '·'
    try:
        f = float(str(v).replace(',', ''))
        if f > 100: f = round(f / 5, 1)
        return str(int(round(f)))
    except: return '·'

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
        yhi  = fv_sel(d.get('2026', (None,None))[0])
        s25, c25 = d.get('2025', (None,None))
        s24, c24 = d.get('2024', (None,None))
        s23, c23 = d.get('2023', (None,None))
        out.append({
            'sido': sido, 'yhi': yhi,
            'se25': fv_sel(s25), 'ct25': fv_cut(c25),
            'se24': fv_sel(s24), 'ct24': fv_cut(c24),
            'se23': fv_sel(s23), 'ct23': fv_cut(c23),
        })
    return out

COLGROUP = (
    '<colgroup>'
    '<col style="width:9mm">'
    '<col style="width:8mm"><col style="width:8mm"><col style="width:8mm">'
    '<col style="width:8mm"><col style="width:8mm">'
    '<col style="width:8mm"><col style="width:8mm">'
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

def make_spread_for_jk(jk, sect_n, label, rows_jk, show_note):
    tr_html = []
    for r in rows_jk:
        tr_html.append(
            f'<tr><td class="sd">{r["sido"]}</td>'
            f'<td class="yhi">{r["yhi"]}</td>'
            f'<td class="se">{r["se25"]}</td><td><b class="ct">{r["ct25"]}</b></td>'
            f'<td class="se">{r["se24"]}</td><td><b class="ct">{r["ct24"]}</b></td>'
            f'<td class="se">{r["se23"]}</td><td><b class="ct">{r["ct23"]}</b></td>'
            f'</tr>'
        )
    note = (
        '<p style="margin-bottom:1.5mm;font-size:var(--fs-sm);">'
        '<b>선</b>=선발(명)·<b class="ct">컷</b>=합격선(과목평균 100점)·'
        '\'26은 선발만··=미선발</p>'
        if show_note else ''
    )
    tbl = (
        f'<table class="extab fix mtx" style="font-size:7pt;width:70mm">'
        f'\n{COLGROUP}\n{HEADER}\n'
        f'<tbody>\n' + '\n'.join(tr_html) + '\n</tbody>\n</table>'
    )
    blk = (
        f'<div class="blk fill"><div class="mh">'
        f'<span class="n mono">{sect_n}</span>'
        f'<h3 class="serif">시·도별 합격선 색인 — {label}</h3>'
        f'<span class="flag real fb">실데이터</span></div>'
        f'<div class="bd">{note}{tbl}</div></div>'
    )
    folio = '<div class="folio"><span class="src">해커스공무원 필기 합격선 배치표</span><span class="pg serif">0</span></div>'
    rhead = '<div class="rhead"><span class="r">PART 4 · 지방 교육행정</span><span>시·도별 합격선 색인</span></div>'
    page = f'<div class="page">\n    {rhead}\n{blk}\n    {folio}\n  </div>'
    return f'\n  <div class="spread">{page}\n  </div>\n'

# 기존 4-3~4-6 spread 제거 후 새 spread 삽입
with open('포켓북_05_교행.html', encoding='utf-8') as f:
    gyohtml = f.read()
seg = gyohtml.split('<!-- SPREADS:START -->')[1].split('<!-- SPREADS:END -->')[0]

oc = re.compile(r'<div\b[^>]*>|</div\s*>')

def find_spread_bounds(seg, sect_ids):
    results = []
    for sect_id in sect_ids:
        pattern = f'class="n mono">{sect_id}</span>'
        pos = 0
        while True:
            idx = seg.find(pattern, pos)
            if idx < 0: break
            sp_start = seg.rfind('<div class="spread">', 0, idx)
            depth = 0; sp_end = None
            for t in oc.finditer(seg, sp_start):
                if t.group().startswith('</div'): depth -= 1
                else: depth += 1
                if depth == 0: sp_end = t.end(); break
            results.append((sp_start, sp_end))
            pos = sp_end
    return sorted(results)

# 4-2 끝 위치
idx42 = seg.find('class="n mono">4-2</span>')
sp42_start = seg.rfind('<div class="spread">', 0, idx42)
depth = 0; end42 = None
for t in oc.finditer(seg, sp42_start):
    if t.group().startswith('</div'): depth -= 1
    else: depth += 1
    if depth == 0: end42 = t.end(); break

# 제거 대상 spread들 (4-3/4-4/4-5/4-6)
remove = find_spread_bounds(seg, ['4-3','4-4','4-5','4-6'])
print(f"제거 대상 spread: {len(remove)}개")

# 새 spread 생성
new_spreads = []
for i, (jk, sect_n, label) in enumerate(JK_CONFIG):
    rows_jk = get_jk_rows(jk)
    print(f'{jk} ({sect_n}): {len(rows_jk)}개 시도')
    if rows_jk:
        new_spreads.append(make_spread_for_jk(jk, sect_n, label, rows_jk, show_note=(i==0)))

# 재조합: seg에서 제거 범위를 뺀 뒤 4-2 다음에 new_spreads 삽입
# 역순으로 제거 (인덱스 유지)
seg_list = list(seg)
for s, e in sorted(remove, reverse=True):
    del seg_list[s:e]
seg_cleaned = ''.join(seg_list)

# end42가 remove로 인해 앞당겨질 수 있으므로 재계산
idx42c = seg_cleaned.find('class="n mono">4-2</span>')
sp42s = seg_cleaned.rfind('<div class="spread">', 0, idx42c)
depth = 0; end42c = None
for t in oc.finditer(seg_cleaned, sp42s):
    if t.group().startswith('</div'): depth -= 1
    else: depth += 1
    if depth == 0: end42c = t.end(); break

new_seg = seg_cleaned[:end42c] + ''.join(new_spreads) + seg_cleaned[end42c:]

# 확인
sects = re.findall(r'<span class="n mono">([^<]+)</span>', new_seg)
print(f"수정 후 spread 목록: {sects}")

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
