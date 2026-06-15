# -*- coding: utf-8 -*-
"""파트별 포켓북 HTML들을 하나로 묶어 '포켓북_전체.html' 생성 (완전한 출력물).

핵심:
- 각 파트의 펼침(.spread) 단위를 읽어, 페이지 1개=단일(표지·간지 등), 2개=설계된 펼침(마주보는 쌍)으로 본다.
- 실제 책 페이지네이션: 표지=오른쪽(recto)부터 시작, 단일면은 recto(오른쪽), 설계된 쌍은 (verso 왼쪽, recto 오른쪽)에 오도록
  필요한 곳에 '빈 페이지(blank)'를 자동 삽입해 홀/짝을 정합한다.
- 화면=두쪽보기(펼침). 표지 왼쪽엔 '표지 안쪽(ifc)' 공백면을 둬서 표지가 오른쪽에 오게 한다(ifc는 인쇄 제외).
- 통합본은 개발/리뷰 흔적(툴바·피드백·상태배지·목업 주석) 모두 제거.
"""
import os, re

PARTS = [
    '포켓북_00_표지.html',
    '포켓북_00b_도비라_목차.html',
    '포켓북_간지_part0.html',     # PART 0 도비라(간지)
    '포켓북_01_길잡이.html',       # PART 0 본문
    '포켓북_간지_part1.html',     # PART 1 도비라(간지) — 국가직 9급
    '포켓북_02_국가직9급.html',   # PART 1 본문
    # 이후 '간지 → 본문' 순으로 계속.
]
OUT = '포켓북_전체.html'

# ── 개발/리뷰 흔적 제거 ──
def clean(seg):
    seg = re.sub(r'<span class="flag[^"]*fb[^"]*">.*?</span>', '', seg)
    seg = re.sub(r'<span class="fb-dot[^"]*">.*?</span>', '', seg)
    seg = seg.replace(' hasfb', '')
    seg = re.sub(r'<div class="dz[^"]*">.*?</div>', '', seg)
    seg = re.sub(r'<div class="dstat">.*?</div>', '', seg)
    seg = re.sub(r'<div class="zone">.*?</div>', '', seg)
    seg = re.sub(r'<div class="sumnote">.*?</div>', '', seg)
    seg = seg.replace(' · <span style="color:var(--muted)">회색 = 예시(목업)</span>', '')
    return seg

# ── 클래스에 특정 토큰을 가진 최상위 div 블록을 깊이추적으로 추출 ──
def extract_divs(html, token):
    res, pos = [], 0
    open_close = re.compile(r'<div\b[^>]*>|</div\s*>')
    head = re.compile(r'<div\b[^>]*\bclass="[^"]*\b' + re.escape(token) + r'\b[^"]*"[^>]*>')
    while True:
        m = head.search(html, pos)
        if not m:
            break
        start = m.start()
        depth = 0
        end = None
        for t in open_close.finditer(html, start):
            if t.group().startswith('</div'):
                depth -= 1
                if depth == 0:
                    end = t.end(); break
            else:
                depth += 1
        if end is None:
            break
        res.append(html[start:end])
        pos = end
    return res

def get_segment(path):
    html = open(path, encoding='utf-8').read()
    seg = html.split('<!-- SPREADS:START -->')[1].split('<!-- SPREADS:END -->')[0]
    return clean(seg)

# ── 모든 페이지를 순서대로 평탄화 ──
pages = []
missing = []
for f in PARTS:
    if not os.path.exists(f):
        missing.append(f); continue
    seg = get_segment(f)
    for sp in extract_divs(seg, 'spread'):
        for pg in extract_divs(sp, 'page'):
            pages.append(pg)

# ── 연속 흐름 페이지네이션 ──
# 표지=1쪽(홀=recto=오른쪽). 이후 자연스럽게 좌우 교대(짝=verso 왼쪽 / 홀=recto 오른쪽).
# 별도 강제 공백 없음 → 파트 간지는 왼쪽(verso), 본문 첫 쪽은 바로 오른쪽(recto)에서 마주봄.
IFC = '<div class="page blank ifc"></div>'   # 표지 안쪽(검토용, 인쇄 제외) → 표지를 오른쪽으로
PAD = '<div class="page blank pad"></div>'   # 마지막 펼침 짝맞춤(검토용, 인쇄 제외)
screen = [IFC] + pages
if len(screen) % 2 == 1:
    screen.append(PAD)
spreads = []
for i in range(0, len(screen), 2):
    spreads.append('  <div class="spread">\n' + screen[i] + '\n' + screen[i+1] + '\n  </div>')
deck = '\n'.join(spreads)
n_phys = len(pages)
n_blank = 0

DOC = f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>합격선 포켓북 — 전체 통합본</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin>
<link rel="stylesheet" href="pocketbook.css">
<style>
  /* 완전한 출력물 — 개발/리뷰용 UI(툴바·피드백)는 통합본에 두지 않는다.
     화면=두쪽보기, 인쇄=개별 A5 낱장(도련 3mm 포함). */
</style>
</head>
<body>

<div class="fitwrap">
<div class="deck" id="deck">
{deck}
</div>
</div>

<script src="pocketbook.js"></script>
</body>
</html>'''

open(OUT, 'w', encoding='utf-8').write(DOC)
print(f'생성: {OUT}')
print(f'  물리 페이지(낱장, 인쇄): {n_phys}쪽')
print(f'  화면 펼침: {len(spreads)}개')
if missing:
    print('  !! 없음:', ', '.join(missing))
