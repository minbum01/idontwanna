# -*- coding: utf-8 -*-
import os as _os
_os.chdir(_os.path.dirname(_os.path.abspath(__file__)))
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
    '포켓북_간지_part2.html',     # PART 2 도비라(간지) — 국가직 7급
    '포켓북_03_국가직7급.html',   # PART 2 본문
    '포켓북_간지_part3.html',     # PART 3 도비라(간지) — 지방직 9급
    '포켓북_04_지방9급.html',     # PART 3 본문
    '포켓북_07_색인.html',        # PART 3 부록 — 시·군 색인 (3-4)
    '포켓북_간지_part4.html',     # PART 4 도비라(간지) — 지방 교육행정
    '포켓북_05_교행.html',        # PART 4 본문
    '포켓북_간지_part5.html',     # PART 5 도비라(간지) — 지방직 7급
    '포켓북_06_지방7급.html',     # PART 5 본문
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

# ── folio(쪽번호) 자동 재부여: 표지 안쪽 제외, 6쪽부터 시작 ──
PAGE_START = 6
for idx in range(len(pages)):
    n = idx + PAGE_START
    pages[idx] = re.sub(r'(<span class="pg serif">)[^<]*(</span>)',
                        lambda m, n=n: m.group(1) + str(n) + m.group(2), pages[idx], count=1)

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

# ── 독립 파일 생성 (CSS·JS 인라인 → 파일 하나로 패드·오프라인에서도 동일하게) ──
OUT_SA = '포켓북_전체_standalone.html'
css_txt = open('pocketbook.css', encoding='utf-8').read()
js_txt  = open('pocketbook.js',  encoding='utf-8').read()

# ── 인쇄용: 각 .page를 cropwrap으로 감싸 재단선 영역(177.65×234.65mm) 추가 ──
# BleedBox(159×216) 주위 각 9.33mm에 재단선(L자 crop marks) 배치
CROP_MARKS = (
    '<span class="cm tl"></span>'
    '<span class="cm tr"></span>'
    '<span class="cm bl"></span>'
    '<span class="cm br"></span>'
)
CROPWRAP_CSS = '''
/* ── 재단선(Crop Marks) — 인쇄 입고용 ── */
.cropwrap{width:177.65mm;height:234.65mm;position:relative;flex-shrink:0;display:flex;align-items:center;justify-content:center;}
.cm{position:absolute;width:7mm;height:7mm;pointer-events:none;}
.cm::before,.cm::after{content:'';position:absolute;background:#000;}
.cm::before{width:5mm;height:.25pt;}
.cm::after{width:.25pt;height:5mm;}
.cm.tl{top:3.33mm;left:3.33mm;}
.cm.tl::before{top:0;left:0;}
.cm.tl::after{top:0;left:0;}
.cm.tr{top:3.33mm;right:3.33mm;}
.cm.tr::before{top:0;right:0;}
.cm.tr::after{top:0;right:0;}
.cm.bl{bottom:3.33mm;left:3.33mm;}
.cm.bl::before{bottom:0;left:0;}
.cm.bl::after{bottom:0;left:0;}
.cm.br{bottom:3.33mm;right:3.33mm;}
.cm.br::before{bottom:0;right:0;}
.cm.br::after{bottom:0;right:0;}
@media screen{.cropwrap{display:contents;}.cm{display:none;}}
@media print{
  @page{size:177.65mm 234.65mm;margin:0;}
  .cropwrap{page-break-after:always;break-after:page;}
  .cropwrap:last-child{page-break-after:auto;break-after:auto;}
  .page{page-break-after:auto !important;break-after:auto !important;}
}
'''

def wrap_pages_for_print(html):
    """각 .page div를 .cropwrap으로 감싸기 (ifc/pad 제외)"""
    import re as _re
    result = []
    pos = 0
    open_close = _re.compile(r'<div\b[^>]*>|</div\s*>')
    page_head = _re.compile(r'<div\b[^>]*\bclass="[^"]*\bpage\b[^"]*"[^>]*>')
    ifc_pad = _re.compile(r'\b(ifc|pad)\b')
    while True:
        m = page_head.search(html, pos)
        if not m:
            result.append(html[pos:])
            break
        result.append(html[pos:m.start()])
        # ifc/pad는 cropwrap 없이 skip
        if ifc_pad.search(m.group()):
            result.append(m.group())
            pos = m.end()
            continue
        # depth로 </div> 찾기
        depth = 0; end = None
        for t in open_close.finditer(html, m.start()):
            depth += (-1 if t.group().startswith('</div') else 1)
            if depth == 0: end = t.end(); break
        page_html = html[m.start():end]
        result.append(f'<div class="cropwrap">{CROP_MARKS}{page_html}</div>')
        pos = end
    return ''.join(result)

DOC_SA = DOC.replace(
    '<link rel="stylesheet" href="pocketbook.css">',
    f'<style>\n{css_txt}\n{CROPWRAP_CSS}\n</style>'
).replace(
    '<script src="pocketbook.js"></script>',
    f'<script>\n{js_txt}\n</script>'
)
DOC_SA = wrap_pages_for_print(DOC_SA)
open(OUT_SA, 'w', encoding='utf-8').write(DOC_SA)
print(f'생성: {OUT_SA}  ← 패드·오프라인용 독립 파일 (재단선 포함)')
