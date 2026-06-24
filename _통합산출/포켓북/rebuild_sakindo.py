# -*- coding: utf-8 -*-
"""rebuild_sakindo.py — RAW v3에서 직접 추출하여 포켓북_07_색인.html 재생성"""
import re, json, sys, io, os
from collections import defaultdict
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ── 0. RAW 로드 ──
with open('../합격선_관리_v3.html', encoding='utf-8') as f:
    html = f.read()
m = re.search(r'const RAW=(\[.*?\]);', html, re.DOTALL)
raw = json.loads(m.group(1))

# ── 1. 상수 정의 ──
SIDOS = ['경기','강원','충북','충남','전북','전남','경북','경남','제주']

BONCHEONG = {
    '경기':  {'경기도'},
    '강원':  {'강원도','강원특별자치도'},
    '충북':  {'충청북도'},
    '충남':  {'충청남도'},
    '전북':  {'전북특별자치도','전라북도'},
    '전남':  {'전라남도'},
    '경북':  {'경상북도'},
    '경남':  {'경상남도'},
    '제주':  {'제주특별자치도','제주도','도'},
}

DO_ABBR = {
    '경기도':'경기', '경상남도':'경남', '경상북도':'경북',
    '충청남도':'충남', '충청북도':'충북',
    '전라남도':'전남', '전라북도':'전북',
    '전북특별자치도':'전북', '강원특별자치도':'강원', '제주특별자치도':'제주',
}

JK_ABBR = {
    '일반행정':'행정', '일반토목':'토목', '일반기계':'기계', '일반전기':'전기',
    '일반농업':'농업', '일반화공':'화공', '일반환경':'환경', '일반수산':'수산',
    '사회복지':'사·복', '보건진료':'보·진', '산림자원':'산·자', '도시계획':'도·계',
    '통신기술':'통·기', '의료기술':'의·기', '농업기계':'농·기', '식품위생':'식·위',
    '시설관리':'시·관', '방송통신':'방·통', '수도토목':'수·목', '기록연구':'기·연',
    '기록관리':'기·관', '해양수산':'해·산', '교통시설':'교·시', '선박항해':'선·항',
    '기계운전':'기·운', '산림보호':'산·보',
}

def abbr_r5(sido, r5):
    r5 = r5.strip()
    if not r5 or r5 in BONCHEONG.get(sido, set()):
        return '본청'
    if '일괄' in r5:
        return '일괄'
    name = r5
    for k, v in DO_ABBR.items():
        name = name.replace(k, v)
    if '의회' in name:
        name = name.replace('의회', '.의')
    return name

def abbr_jk(jk):
    return JK_ABBR.get(jk, jk)

def make_gwan(sido, r5, jk):
    return abbr_r5(sido, r5) + '·' + abbr_jk(jk)

# ── 2. 필터 및 집계 ──
def is_target(r):
    if r[0] not in SIDOS or r[2] not in ('2023','2024','2025','2026'): return False
    if r[4] != '공개경쟁' or r[10] != '일반' or r[9] != '9급' or r[1] != '공무원': return False
    jk = r[8].strip()
    if '(장)' in jk or '(저)' in jk: return False
    return True

rows = [r for r in raw if is_target(r)]

def fv(v, is_cut=False):
    try:
        f = float(str(v).replace(',',''))
        return str(int(round(f)))
    except:
        return '·'

data = defaultdict(lambda: defaultdict(lambda: (None, None)))
for r in rows:
    key = (r[0], r[5].strip(), r[8].strip())
    yr = r[2]
    if data[key][yr] == (None, None):
        data[key][yr] = (r[11], r[18])

print(f'유니크 (시도·기관·직류): {len(data)}')

# ── 3. 시도별 정렬 및 그룹화 ──
groups = {}
for sido in SIDOS:
    keys_s = [(k, d) for k, d in data.items() if k[0] == sido]

    # 기관별 2025 선발 합산 → 내림차순
    gwan_sel25 = defaultdict(int)
    for (s, r5, jk), d in keys_s:
        try:
            gwan_sel25[r5] += int(float(str(d.get('2025',(None,None))[0] or 0)))
        except:
            pass

    gwans_sorted = sorted(gwan_sel25.keys())  # 가나다순

    rows_out = []
    for g in gwans_sorted:
        items = [(jk, d) for (s, r5, jk), d in keys_s if r5 == g]
        items.sort(key=lambda x: -(
            int(float(str(x[1].get('2025',(None,None))[0] or 0)))
            if x[1].get('2025',(None,None))[0] else 0
        ))
        for jk, d in items:
            gwan_disp = make_gwan(sido, g, jk)
            yhi = fv(d.get('2026',(None,None))[0])
            se25, ct25 = d.get('2025', (None,None))
            se24, ct24 = d.get('2024', (None,None))
            se23, ct23 = d.get('2023', (None,None))
            rows_out.append({
                'sido': sido, 'gwan': gwan_disp,
                'yhi':  yhi,
                'se25': fv(se25), 'ct25': fv(ct25),
                'se24': fv(se24), 'ct24': fv(ct24),
                'se23': fv(se23), 'ct23': fv(ct23),
            })
    groups[sido] = rows_out

for sido in SIDOS:
    print(f'  {sido}: {len(groups[sido])}행')

# ── 4. HTML 상수 ──
COLGROUP = (
    '<colgroup>'
    '<col style="width:6mm"><col style="width:14mm"><col>'
    '<col><col><col><col><col><col>'
    '<col style="width:1.4mm">'
    '<col style="width:6mm"><col style="width:14mm"><col>'
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
    '<td class="se"></td><td></td><td class="se"></td><td></td>'
    '<td class="se"></td><td></td>'
)

def make_entry(r):
    return (
        f'<td class="sd">{r["sido"]}</td>'
        f'<td class="gw">{r["gwan"]}</td>'
        f'<td class="yhi">{r["yhi"]}</td>'
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
        left = make_entry(items[i]); i += 1
        right = make_entry(items[i]) if i < len(items) else EMPTY
        if i < len(items): i += 1
        html_rows.append(f'<tr>{left}<td class="spc"></td>{right}</tr>')

    note = (
        '<p style="margin-bottom:1mm;font-size:var(--fs-sm);">'
        '<b>선</b>=선발(명)·<b class="ct">컷</b>=합격선(과목평균 100점)·'
        '\'26은 선발만·빈칸(·)=미모집</p>'
        if show_note else ''
    )
    table_html = (
        f'<table class="extab fix mtx idx sgun sg3 city" style="font-size:5.9pt;">'
        f'\n{COLGROUP}\n{HEADER}\n'
        f'<tbody>\n' + '\n'.join(html_rows) + '\n</tbody>\n</table>'
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

# ── 5. 도별 spread 생성 ──
with open('포켓북_07_색인.html', encoding='utf-8') as f:
    h = f.read()
seg = h.split('<!-- SPREADS:START -->')[1].split('<!-- SPREADS:END -->')[0]

spreads_html = []
first_ever = True
ITEMS_PER_PAGE = ROWS_PER_PAGE * 2

for sido in SIDOS:
    items = groups[sido]
    if not items:
        continue
    n = len(items)
    total_pages = max(1, (n + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
    for p in range(total_pages):
        chunk = items[p * ITEMS_PER_PAGE : (p+1) * ITEMS_PER_PAGE]
        label = sido if total_pages == 1 else f'{sido} ({p+1}/{total_pages})'
        spreads_html.append(make_spread(chunk, label, label, show_note=first_ever))
        first_ever = False

print(f'지방9·8급 spread: {len(spreads_html)}개')

# ── 6. 저장 ──
all_spreads = spreads_html
new_h = (
    h.split('<!-- SPREADS:START -->')[0]
    + '<!-- SPREADS:START -->'
    + ''.join(all_spreads)
    + '<!-- SPREADS:END -->'
    + h.split('<!-- SPREADS:END -->')[1]
)
with open('포켓북_07_색인.html', 'w', encoding='utf-8') as f:
    f.write(new_h)
print(f'저장 완료 — 총 spread: {len(all_spreads)}')
