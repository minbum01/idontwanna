# -*- coding: utf-8 -*-
"""교행 시·도별 합격선 색인 rebuild
   지방9급 색인처럼 2단 테이블, 직류별 소타이틀 행으로 구분
   spread 1개 (4-3) 안에 교육행정/사서/전산/건축 전부
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

JK_LIST = ['교육행정', '사서', '전산', '건축']

def fv_sel(v):
    if v in (None, ''): return '·'
    try: return str(int(round(float(str(v).replace(',', '')))))
    except: return '·'

def fv_cut(v):
    if v in (None, ''): return '·'
    try:
        f = float(str(v).replace(',', ''))
        if f > 100: f = f / 5
        return f'{f:.1f}'
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

# 2단 테이블 상수 (지방9급과 동일 구조)
COLGROUP = (
    '<colgroup>'
    '<col style="width:7mm"><col style="width:6mm">'
    '<col style="width:6mm"><col style="width:6mm">'
    '<col style="width:6mm"><col style="width:6mm">'
    '<col style="width:6mm"><col style="width:6mm">'
    '<col style="width:1.4mm">'
    '<col style="width:7mm"><col style="width:6mm">'
    '<col style="width:6mm"><col style="width:6mm">'
    '<col style="width:6mm"><col style="width:6mm">'
    '<col style="width:6mm"><col style="width:6mm">'
    '</colgroup>'
)
HEADER = (
    '<thead><tr>'
    '<th rowspan="2">시도</th>'
    '<th class="grp" rowspan="2">\'26<br>선</th>'
    '<th colspan="2" class="grp">\'25</th>'
    '<th colspan="2" class="grp">\'24</th>'
    '<th colspan="2" class="grp">\'23</th>'
    '<th class="spc" rowspan="2"></th>'
    '<th rowspan="2">시도</th>'
    '<th class="grp" rowspan="2">\'26<br>선</th>'
    '<th colspan="2" class="grp">\'25</th>'
    '<th colspan="2" class="grp">\'24</th>'
    '<th colspan="2" class="grp">\'23</th>'
    '</tr><tr>'
    '<th class="grp">선</th><th class="ct">컷</th>'
    '<th class="grp">선</th><th class="ct">컷</th>'
    '<th class="grp">선</th><th class="ct">컷</th>'
    '<th class="grp">선</th><th class="ct">컷</th>'
    '<th class="grp">선</th><th class="ct">컷</th>'
    '<th class="grp">선</th><th class="ct">컷</th>'
    '</tr></thead>'
)
EMPTY = (
    '<td class="sd"></td><td class="yhi"></td>'
    '<td class="se"></td><td></td>'
    '<td class="se"></td><td></td>'
    '<td class="se"></td><td></td>'
)

def make_entry(r):
    return (
        f'<td class="sd">{r["sido"]}</td>'
        f'<td class="yhi">{r["yhi"]}</td>'
        f'<td class="se">{r["se25"]}</td><td><b class="ct">{r["ct25"]}</b></td>'
        f'<td class="se">{r["se24"]}</td><td><b class="ct">{r["ct24"]}</b></td>'
        f'<td class="se">{r["se23"]}</td><td><b class="ct">{r["ct23"]}</b></td>'
    )

# 아이템 목록 생성 (소타이틀 포함)
items = []
for jk in JK_LIST:
    jk_rows = get_jk_rows(jk)
    print(f'{jk}: {len(jk_rows)}개 시도')
    if not jk_rows: continue
    items.append({'type': 'header', 'label': jk})
    for r in jk_rows:
        items.append({'type': 'row', 'data': r})

# 2단 배치 — 소타이틀은 colspan 17
tr_html = []
i = 0
while i < len(items):
    item = items[i]
    if item['type'] == 'header':
        tr_html.append(
            f'<tr><td colspan="17" style="'
            f'font-size:6pt;font-weight:700;padding:1.5mm 1mm 0.5mm;'
            f'background:#eaf0fb;color:#1a3a6b;border-bottom:0.5pt solid #7da3d6">'
            f'{item["label"]}</td></tr>'
        )
        i += 1
    else:
        left = make_entry(item['data']); i += 1
        if i < len(items) and items[i]['type'] == 'row':
            right = make_entry(items[i]['data']); i += 1
        else:
            right = EMPTY
        tr_html.append(f'<tr>{left}<td class="spc"></td>{right}</tr>')

total_data = sum(1 for it in items if it['type']=='row')
print(f'총 데이터 행: {total_data}, TR 수: {len(tr_html)}')

# spread HTML 생성
note = (
    '<p style="margin-bottom:1mm;font-size:var(--fs-sm);">'
    '공개채용 일반 기준 · <b>선</b>=선발(명) · <b class="ct">컷</b>=합격선(과목평균 100점) · '
    '\'26은 선발만 · 빈칸(·)=미모집</p>'
)
tbl = (
    f'<table class="extab fix mtx idx sgun city" style="font-size:6pt;">'
    f'\n{COLGROUP}\n{HEADER}\n'
    f'<tbody>\n' + '\n'.join(tr_html) + '\n</tbody>\n</table>'
)
blk = (
    '<div class="blk fill"><div class="mh">'
    '<span class="n mono">4-3</span>'
    '<h3 class="serif">시·도별 합격선 색인</h3>'
    '<span class="flag real fb">실데이터</span></div>'
    f'<div class="bd">{note}{tbl}</div></div>'
)
folio = '<div class="folio"><span class="src">해커스공무원 필기 합격선 배치표</span><span class="pg serif">0</span></div>'
rhead = '<div class="rhead"><span class="r">PART 4 · 지방 교육행정</span><span>합격선 색인</span></div>'
page = f'<div class="page">\n    {rhead}\n{blk}\n    {folio}\n  </div>'
spread_html = f'\n  <div class="spread">{page}\n  </div>\n'

# 05_교행.html 업데이트
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
sp42s = seg.rfind('<div class="spread">', 0, idx42)
depth = 0; end42 = None
for t in oc.finditer(seg, sp42s):
    if t.group().startswith('</div'): depth -= 1
    else: depth += 1
    if depth == 0: end42 = t.end(); break

# 기존 4-3~4-6 제거
remove = find_spread_bounds(seg, ['4-3','4-4','4-5','4-6'])
print(f"제거 대상: {len(remove)}개")
seg_list = list(seg)
for s, e in sorted(remove, reverse=True):
    del seg_list[s:e]
seg_cleaned = ''.join(seg_list)

# 4-2 끝 재계산
idx42c = seg_cleaned.find('class="n mono">4-2</span>')
sp42sc = seg_cleaned.rfind('<div class="spread">', 0, idx42c)
depth = 0; end42c = None
for t in oc.finditer(seg_cleaned, sp42sc):
    if t.group().startswith('</div'): depth -= 1
    else: depth += 1
    if depth == 0: end42c = t.end(); break

new_seg = seg_cleaned[:end42c] + spread_html + seg_cleaned[end42c:]
sects = re.findall(r'<span class="n mono">([^<]+)</span>', new_seg)
print(f"spread 목록: {sects}")

new_html = (
    gyohtml.split('<!-- SPREADS:START -->')[0]
    + '<!-- SPREADS:START -->'
    + new_seg
    + '<!-- SPREADS:END -->'
    + gyohtml.split('<!-- SPREADS:END -->')[1]
)
with open('포켓북_05_교행.html', 'w', encoding='utf-8') as f:
    f.write(new_html)
print('저장 완료')
