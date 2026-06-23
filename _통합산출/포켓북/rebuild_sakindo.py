# -*- coding: utf-8 -*-
import re, sys, io, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ── 1. 기존 색인에서 모든 데이터 추출 ──
with open('포켓북_07_색인.html', encoding='utf-8') as f:
    h = f.read()
seg = h.split('<!-- SPREADS:START -->')[1].split('<!-- SPREADS:END -->')[0]

rows_all = []
for tbody_m in re.finditer(r'<tbody>(.*?)</tbody>', seg, re.DOTALL):
    tbody = tbody_m.group(1)
    for row_m in re.finditer(r'<tr[^>]*>(.*?)</tr>', tbody, re.DOTALL):
        row = row_m.group(1)
        if 'city-gap' in row_m.group(0):
            continue
        cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
        cells = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]
        if len(cells) < 9:
            continue
        for side in [(0,1,2,3,4,5,6,7,8), (10,11,12,13,14,15,16,17,18)]:
            if max(side) >= len(cells):
                continue
            i0,i1,i2,i3,i4,i5,i6,i7,i8 = side
            sido = cells[i0]; gwan = cells[i1]
            if not sido or not gwan:
                continue
            rows_all.append({
                'sido': sido, 'gwan': gwan, 'yhi': cells[i2],
                'se25': cells[i3], 'ct25': cells[i4],
                'se24': cells[i5], 'ct24': cells[i6],
                'se23': cells[i7], 'ct23': cells[i8],
            })

print(f'추출 항목: {len(rows_all)}개')

# ── 2. 도별 정렬 ──
# 광역시·특별시는 3-3 시 단위 색인에 이미 있으므로 제외
SIDOS = ['경기','강원','충북','충남','전북','전남','경북','경남','제주']

def yhi_int(r):
    try:
        return int(float(r['yhi'] or 0))
    except:
        return 0

groups = {}
for sido in SIDOS:
    g = [r for r in rows_all if r['sido'] == sido]
    g.sort(key=lambda r: -yhi_int(r))
    groups[sido] = g

sidos_have = [s for s in SIDOS if groups.get(s)]

# ── 3. HTML 상수 ──
COLGROUP = (
    '<colgroup>'
    '<col style="width:6mm"><col style="width:13mm"><col>'
    '<col><col><col><col><col><col>'
    '<col style="width:1.4mm">'
    '<col style="width:6mm"><col style="width:13mm"><col>'
    '<col><col><col><col><col><col>'
    '</colgroup>'
)

HEADER = (
    '<thead><tr>'
    '<th rowspan="2">시도</th><th rowspan="2">기관</th>'
    '<th class="grp" rowspan="2">\'26<br>선</th>'
    '<th colspan="2" class="grp">\'25</th>'
    '<th colspan="2" class="grp">\'24</th>'
    '<th colspan="2" class="grp">\'23</th>'
    '<th class="spc" rowspan="2"></th>'
    '<th rowspan="2">시도</th><th rowspan="2">기관</th>'
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
    '<td class="se"></td><td></td><td class="se"></td><td></td>'
    '<td class="se"></td><td></td>'
)

GAP_ROW = (
    '<tr class="city-gap">'
    '<td class="sd"></td><td class="gw"></td><td class="yhi"></td>'
    '<td class="se"></td><td></td><td class="se"></td><td></td>'
    '<td class="se"></td><td></td><td class="spc"></td>'
    '<td class="sd"></td><td class="gw"></td><td class="yhi"></td>'
    '<td class="se"></td><td></td><td class="se"></td><td></td>'
    '<td class="se"></td><td></td></tr>'
)

def make_entry(r):
    yhi = r['yhi'] if r['yhi'] not in ('', None) else '·'
    return (
        f'<td class="sd">{r["sido"]}</td>'
        f'<td class="gw">{r["gwan"]}</td>'
        f'<td class="yhi">{yhi}</td>'
        f'<td class="se">{r["se25"]}</td><td><b class="ct">{r["ct25"]}</b></td>'
        f'<td class="se">{r["se24"]}</td><td><b class="ct">{r["ct24"]}</b></td>'
        f'<td class="se">{r["se23"]}</td><td><b class="ct">{r["ct23"]}</b></td>'
    )

ROWS_PER_PAGE = 44

def make_spread(chunk, sido_label, part_str, show_note=False):
    html_rows = []
    i = 0
    items = list(chunk)
    while i < len(items):
        item = items[i]
        left = make_entry(item)
        i += 1
        if i < len(items):
            right = make_entry(items[i])
            i += 1
        else:
            right = EMPTY
        html_rows.append(f'<tr>{left}<td class="spc"></td>{right}</tr>')

    tbody_content = '\n'.join(html_rows)
    table_html = (
        f'<table class="extab fix mtx idx sgun sg3 city" style="font-size:5.9pt;">'
        f'\n{COLGROUP}\n{HEADER}\n'
        f'<tbody>\n{tbody_content}\n</tbody>\n</table>'
    )
    note = (
        '<p style="margin-bottom:1mm;font-size:var(--fs-sm);">'
        '<b>선</b>=선발(명)·<b class="ct">컷</b>=합격선(과목평균 100점)·'
        "'26은 선발만·빈칸(·)=미모집</p>"
        if show_note else ''
    )
    blk = (
        f'<div class="blk fill"><div class="mh">'
        f'<span class="n mono">3-7</span>'
        f'<h3 class="serif">지방 9·8급 시·군 색인 — {sido_label}</h3>'
        f'<span class="flag real fb">실데이터</span></div>'
        f'<div class="bd">{note}{table_html}</div></div>'
    )
    folio = '<div class="folio"><span class="src">해커스공무원 필기 합격선 배치표</span><span class="pg serif">0</span></div>'
    rhead = f'<div class="rhead"><span class="r">데이터 색인</span><span>지방 9·8급 {part_str}</span></div>'
    page = f'<div class="page">\n    {rhead}\n{blk}\n    {folio}\n  </div>'
    return f'\n  <div class="spread">{page}\n  </div>\n'

# ── 4. 도별 spread 생성 ──
spreads_html = []
first_ever = True
for sido in sidos_have:
    items = groups[sido]
    n = len(items)
    items_per_page = ROWS_PER_PAGE * 2  # 2열
    total_pages = max(1, (n + items_per_page - 1) // items_per_page)

    for p in range(total_pages):
        start_idx = p * items_per_page
        end_idx = min(start_idx + items_per_page, n)
        chunk = items[start_idx:end_idx]
        if total_pages == 1:
            label = sido
            part_str = sido
        else:
            label = f'{sido} ({p+1}/{total_pages})'
            part_str = label
        sp = make_spread(chunk, label, part_str, show_note=first_ever)
        spreads_html.append(sp)
        first_ever = False

print(f'지방9·8급 spread 수: {len(spreads_html)}')

# ── 5. 교육행정·지방7급 spread 유지 ──
def extract_spreads_by_sect(html_seg, sect_id):
    results = []
    pos = 0
    oc = re.compile(r'<div\b[^>]*>|</div\s*>')
    head_pat = re.compile(r'<div\b[^>]*\bclass="[^"]*\bspread\b[^"]*"[^>]*>')
    while True:
        idx = html_seg.find(f'<span class="n mono">{sect_id}</span>', pos)
        if idx < 0:
            break
        sp_start = html_seg.rfind('<div class="spread">', 0, idx)
        depth = 0; end = None
        for t in oc.finditer(html_seg, sp_start):
            if t.group().startswith('</div'):
                depth -= 1
                if depth == 0:
                    end = t.end()
                    break
            else:
                depth += 1
        if end is None:
            break
        results.append('\n  ' + html_seg[sp_start:end] + '\n')
        pos = end
    return results

gyohaeng_spreads = extract_spreads_by_sect(seg, '4-6')
jibang7_spreads  = extract_spreads_by_sect(seg, '5-6')
print(f'교육행정: {len(gyohaeng_spreads)}, 지방7급: {len(jibang7_spreads)}')

# ── 6. 최종 조합 및 저장 ──
all_spreads = spreads_html + gyohaeng_spreads + jibang7_spreads
full_seg = ''.join(all_spreads)
print(f'최종 spread 합계: {len(all_spreads)}')

new_h = (
    h.split('<!-- SPREADS:START -->')[0]
    + '<!-- SPREADS:START -->'
    + full_seg
    + '<!-- SPREADS:END -->'
    + h.split('<!-- SPREADS:END -->')[1]
)
with open('포켓북_07_색인.html', 'w', encoding='utf-8') as f:
    f.write(new_h)
print('저장 완료')
