# -*- coding: utf-8 -*-
"""포켓북 연도표를 '최근 연도 왼쪽(내림차순)'으로 뒤집고, 2026 열에 연파랑(.yhi) 표시.
- 오름차순 연도표만 뒤집음(이미 내림차순인 표는 건너뜀 → 중복 적용 안전).
- 대상: 인자로 받은 파일들."""
import re, sys

def col_year(cell):
    t = re.sub(r'<[^>]+>', '', cell)
    m = re.search(r"20(\d\d)|[’'](\d\d)", t)
    if not m: return None
    return 2000 + int(m.group(1) or m.group(2))

def add_cls(cell, tag, cls):
    m = re.match(r'<' + tag + r'\b([^>]*)>', cell)
    if not m: return cell
    attrs = m.group(1)
    if cls in re.findall(r'class="([^"]*)"', attrs) or (' '+cls) in attrs or ('"'+cls) in attrs:
        return cell                      # 이미 태깅됨 → 멱등
    if 'class="' in attrs:
        attrs = re.sub(r'class="([^"]*)"', lambda mm: f'class="{mm.group(1)} {cls}"', attrs, count=1)
    else:
        attrs = attrs + f' class="{cls}"'
    return f'<{tag}{attrs}>' + cell[m.end():]

def process_table(m):
    tbl = m.group(0)
    thm = re.search(r'<thead><tr>(.*?)</tr></thead>', tbl, re.S)
    if not thm: return tbl
    ths = re.findall(r'<th\b[^>]*>.*?</th>', thm.group(1))
    yidx = [i for i, th in enumerate(ths) if col_year(th)]
    if len(yidx) < 2: return tbl
    yvals = [col_year(ths[i]) for i in yidx]
    asc  = yvals == sorted(yvals)
    desc = yvals == sorted(yvals, reverse=True)
    if not asc and not desc:           # 단조롭지 않으면 건드리지 않음
        return tbl
    def rev(cells):
        out = cells[:]
        r = [cells[i] for i in reversed(yidx)]
        for p, i in enumerate(yidx): out[i] = r[p]
        return out
    new_ths = rev(ths) if asc else ths[:]    # 오름차순만 뒤집기, 내림차순은 태깅만
    hi = None
    for i, th in enumerate(new_ths):
        if col_year(th) == 2026:
            hi = i; new_ths[i] = add_cls(new_ths[i], 'th', 'yhi')
    out = tbl.replace(thm.group(0), '<thead><tr>' + ''.join(new_ths) + '</tr></thead>', 1)
    tbm = re.search(r'<tbody>(.*?)</tbody>', out, re.S)
    if tbm:
        def fix_tr(rm):
            row = rm.group(0)
            tds = re.findall(r'<td\b[^>]*>.*?</td>', rm.group(1))
            if len(tds) != len(ths): return row
            nt = rev(tds) if asc else tds[:]
            if hi is not None: nt[hi] = add_cls(nt[hi], 'td', 'yhi')
            pre = row[:row.index('>') + 1]
            return pre + ''.join(nt) + '</tr>'
        nb = re.sub(r'<tr\b[^>]*>(.*?)</tr>', fix_tr, tbm.group(1), flags=re.S)
        out = out.replace('<tbody>' + tbm.group(1) + '</tbody>', '<tbody>' + nb + '</tbody>', 1)
    return out

for path in sys.argv[1:]:
    html = open(path, encoding='utf-8').read()
    n_before = len(re.findall(r"<th[^>]*>’23</th>|<th[^>]*>2023</th>", html))
    html = re.sub(r'<table\b[^>]*>.*?</table>', process_table, html, flags=re.S)
    open(path, 'w', encoding='utf-8').write(html)
    print(f"{path}: 처리 완료 (연도표 후보 {n_before})")
