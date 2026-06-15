# -*- coding: utf-8 -*-
"""파트별 포켓북 HTML들을 하나로 묶어 '포켓북_전체.html' 생성.
각 파트 파일의 <!-- SPREADS:START --> ~ <!-- SPREADS:END --> 사이(펼침면)를 추출해 이어붙인다.
새 파트가 생기면 아래 PARTS 목록에 추가하고 다시 실행."""
import os

PARTS = [
    '포켓북_00_표지.html',
    '포켓북_01_길잡이.html',
    # 여기에 파트 추가: '포켓북_02_직렬별전국비교.html', ...
]
OUT = '포켓북_전체.html'

spreads = []
for f in PARTS:
    if not os.path.exists(f):
        print('!! 없음, 건너뜀:', f); continue
    html = open(f, encoding='utf-8').read()
    try:
        seg = html.split('<!-- SPREADS:START -->')[1].split('<!-- SPREADS:END -->')[0]
    except IndexError:
        print('!! 마커 없음, 건너뜀:', f); continue
    spreads.append('  <!-- ===== ' + f + ' ===== -->\n' + seg.strip('\n'))

deck = '\n\n'.join(spreads)
n_spreads = deck.count('<div class="spread">')

DOC = f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>필기 합격선 배치표 — 전체 통합본</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin>
<link rel="stylesheet" href="pocketbook.css">
<style>
  /* 표지 등 낱장 페이지가 섞여도 인쇄는 펼침(A4 가로) 기준 — 화면 미리보기 위주 */
  .partsep{{display:none;}}
</style>
</head>
<body>

<div class="toolbar">
  <div><b>필기 합격선 배치표</b> · 전체 통합본 <span class="meta">— {len(spreads)}개 파트 · 펼침면 {n_spreads}개 · 자동생성</span></div>
  <div class="btns">
    <button class="b-fb" id="fbBtn" onclick="toggleFb()">⚑ 피드백 보기</button>
    <button class="b-print" onclick="window.print()">🖨 인쇄 / PDF</button>
  </div>
</div>

<div class="fitwrap">
<div class="deck" id="deck">
{deck}
</div>
</div>

<script src="pocketbook.js"></script>
</body>
</html>'''

open(OUT, 'w', encoding='utf-8').write(DOC)
print('생성:', OUT, '| 파트', len(spreads), '| 펼침면', n_spreads)
