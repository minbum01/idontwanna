# -*- coding: utf-8 -*-
"""교행 4-4 색인 rebuild: 4-4 매트릭스 spread → 시·군별 색인 spread"""
import re, json, sys, io, os
from collections import defaultdict
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('../합격선_관리_v3.html', encoding='utf-8') as f:
    html = f.read()
m = re.search(r'const RAW=(\[.*?\]);', html, re.DOTALL)
raw = json.loads(m.group(1))

def is_gyo(r):
    if r[1] != '공무원' or r[4] != '공개경쟁' or r[10] != '일반': return False
    if r[9] != '9급': return False
    if r[8] not in ('교육행정', '사서', '시설'): return False
    if r[2] not in ('2023', '2024', '2025', '2026'): return False
    return True

rows = [r for r in raw if is_gyo(r)]

SIDO_ORDER = ['서울','부산','대구','인천','광주','대전','울산','세종',
              '경기','강원','충북','충남','전북','전남','경북','경남','제주']
JK_ORDER = {'교육행정': 0, '사서': 1, '시설': 2}
GYO_JK   = {'교육행정': '교행', '사서': '사서', '시설': '시설'}

def fv(v):
    if v in (None, ''): return '·'
    try:
        return str(int(round(float(str(v).replace(',', '')))))
    except:
        return '·'

def make_gwan(r5, jk):
    r5 = r5.strip()
    jk_a = GYO_JK.get(jk, jk)
    if not r5: return jk_a
    if any(x in r5 for x in ['시·구', '및', '일괄']): return jk_a
    return r5 + '·' + jk_a

# 집계
data = defaultdict(dict)
for r in rows:
    key = (r[0], r[5].strip(), r[8].strip())
    yr = r[2]
    if yr not in data[key]:
        data[key][yr] = (r[11], r[18])

def get_sido_rows(sido):
    ks = [(k, d) for k, d in data.items() if k[0] == sido]
    gwan_sel = defaultdict(int)
    for (k, d) in ks:
        r5 = k[1]
        try: gwan_sel[r5] += int(float(str(d.get('2026', (None, None))[0] or 0)))
        except: pass
    gwans = sorted(set(k[1] for k, _ in ks), key=lambda g: -gwan_sel[g])
    out = []
    for g in gwans:
        items = [(k[2], d) for k, d in ks if k[1] == g]
        items.sort(key=lambda x: JK_ORDER.get(x[0], 9))
        for jk, d in items:
            s25, c25 = d.get('2025', (None, None))
            s24, c24 = d.get('2024', (None, None))
            s23, c23 = d.get('2023', (None, None))
            yhi = fv(d.get('2026', (None, None))[0])
            out.append({
                'sido': sido, 'gwan': make_gwan(g, jk), 'yhi': yhi,
                'se25': fv(s25), 'ct25': fv(c25),
                'se24': fv(s24), 'ct24': fv(c24),
                'se23': fv(s23), 'ct23': fv(c23),
            })
    return out

class Gap: pass

all_items = []
for sido in SIDO_ORDER:
    rs = get_sido_rows(sido)
    if not rs: continue
    if all_items: all_items.append(Gap())
    all_items.extend(rs)

real_count = sum(1 for x in all_items if not isinstance(x, Gap))
print(f'총 {real_count}항목 (gap 포함 {len(all_items)})')

COLGROUP = (
    '<colgroup>'
    '<col style="width:5mm"><col style="width:15mm"><col>'
    '<col><col><col><col><col><col>'
    '<col style="width:1.4mm">'
    '<col style="width:5mm"><col style="width:15mm"><col>'
    '<col><col><col><col><col><col>'
    '</colgroup>'
)
HEADER = (
    '<thead><tr>'
    '<th rowspan="2">시도</th><th rowspan="2">기관·직류</th>'
    '<th class="grp" rowspan="2">\'26<br>선</th>'
    '<th colspan="2" class="grp">\'25</th>'
    '<th colspan="2" class="grp">\'24</th>'
    '<th colspan="2" class="grp">\'23</th>'
    '<th class="spc" rowspan="2"></th>'
    '<th rowspan="2">시도</th><th rowspan="2">기관·직류</th>'
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
    '<td class="sd"></td><td class="gw"></td><td class="yhi"></td>'
    '<td class="se"></td><td></td><td class="se"></td><td></td><td class="se"></td><td></td>'
)
GAP_ROW = '<tr class="city-gap"><td colspan="9"></td><td class="spc"></td><td colspan="9"></td></tr>'

def entry(r):
    return (
        f'<td class="sd">{r["sido"]}</td><td class="gw">{r["gwan"]}</td>'
        f'<td class="yhi">{r["yhi"]}</td>'
        f'<td class="se">{r["se25"]}</td><td><b class="ct">{r["ct25"]}</b></td>'
        f'<td class="se">{r["se24"]}</td><td><b class="ct">{r["ct24"]}</b></td>'
        f'<td class="se">{r["se23"]}</td><td><b class="ct">{r["ct23"]}</b></td>'
    )

def make_spread_html(chunk, label, show_note):
    html_rows = []
    i = 0
    items_list = list(chunk)
    while i < len(items_list):
        item = items_list[i]
        if isinstance(item, Gap):
            html_rows.append(GAP_ROW)
            i += 1
            continue
        left = entry(item)
        i += 1
        if i < len(items_list) and not isinstance(items_list[i], Gap):
            right = entry(items_list[i])
            i += 1
        else:
            right = EMPTY
        html_rows.append(f'<tr>{left}<td class="spc"></td>{right}</tr>')

    note = (
        '<p style="margin-bottom:1mm;font-size:var(--fs-sm);">'
        '<b>선</b>=선발(명)·<b class="ct">컷</b>=합격선(100점)·\'26은 선발만··=미모집</p>'
        if show_note else ''
    )
    tbl = (
        f'<table class="extab fix mtx idx sgun sg3 city" style="font-size:5.9pt;">'
        f'\n{COLGROUP}\n{HEADER}\n'
        f'<tbody>\n' + '\n'.join(html_rows) + '\n</tbody>\n</table>'
    )
    blk = (
        f'<div class="blk fill"><div class="mh">'
        f'<span class="n mono">4-4</span>'
        f'<h3 class="serif">시·군별 합격선 색인 — {label}</h3>'
        f'<span class="flag real fb">실데이터</span></div>'
        f'<div class="bd">{note}{tbl}</div></div>'
    )
    folio = '<div class="folio"><span class="src">해커스공무원 필기 합격선 배치표</span><span class="pg serif">0</span></div>'
    rhead = '<div class="rhead"><span class="r">PART 4 · 지방 교육행정</span><span>시·군별 합격선 색인</span></div>'
    page = f'<div class="page">\n    {rhead}\n{blk}\n    {folio}\n  </div>'
    return f'\n  <div class="spread">{page}\n  </div>\n'

# 청크 분할 (spread당 88 실데이터)
DATA_PER_SPREAD = 88

def split_chunks(all_items):
    chunks = []
    current = []
    real_cnt = 0
    for item in all_items:
        if isinstance(item, Gap):
            current.append(item)
        else:
            real_cnt += 1
            current.append(item)
            if real_cnt >= DATA_PER_SPREAD:
                chunks.append(current)
                current = []
                real_cnt = 0
    if current:
        chunks.append(current)
    return chunks

chunks = split_chunks(all_items)
print(f'spread 수: {len(chunks)}')
for ci, ch in enumerate(chunks):
    rc = sum(1 for x in ch if not isinstance(x, Gap))
    first = next((x['sido'] for x in ch if not isinstance(x, Gap)), '')
    last  = next((x['sido'] for x in reversed(ch) if not isinstance(x, Gap)), '')
    print(f'  chunk{ci}: {rc}항목 {first}~{last}')

# 05_교행.html 수정
with open('포켓북_05_교행.html', encoding='utf-8') as f:
    gyohtml = f.read()
seg = gyohtml.split('<!-- SPREADS:START -->')[1].split('<!-- SPREADS:END -->')[0]

idx44 = seg.find('"4-4"')
sp_start = seg.rfind('<div class="spread">', 0, idx44)
oc = re.compile(r'<div\b[^>]*>|</div\s*>')
depth = 0
sp_end = None
for t in oc.finditer(seg, sp_start):
    if t.group().startswith('</div'):
        depth -= 1
    else:
        depth += 1
    if depth == 0:
        sp_end = t.end()
        break

new_spreads = []
for ci, ch in enumerate(chunks):
    first = next((x['sido'] for x in ch if not isinstance(x, Gap)), '')
    last  = next((x['sido'] for x in reversed(ch) if not isinstance(x, Gap)), '')
    label = first if first == last else f'{first}~{last}'
    new_spreads.append(make_spread_html(ch, label, ci == 0))

new_spread_str = ''.join(new_spreads)
new_seg = seg[:sp_start] + new_spread_str + seg[sp_end:]
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
