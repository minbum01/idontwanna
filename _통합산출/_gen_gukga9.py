# -*- coding: utf-8 -*-
"""검증_data.csv의 국가직 9급 → 포켓북 PART 1 본문(4쪽) 생성: 포켓북_02_국가직9급.html
① 4개년 요약 ② TOP 5 직렬 ③ 전체 직류 합격선(행정직군) ④ 전체 직류 합격선(기술직군)+지역구분"""
import csv, os
from collections import defaultdict
D = os.path.dirname(__file__)
rows = list(csv.DictReader(open(os.path.join(D,"검증_data.csv"), encoding="utf-8-sig")))
g9 = [r for r in rows if r["지역"]=="국가직" and r["직급"]=="9급"]
Y = ["2023","2024","2025","2026"]

def num(s):
    s=(s or "").replace(",","").strip()
    try: return float(s)
    except: return 0
def comma(n): return f"{int(round(n)):,}"
def cut(s):  # 90.00 -> 90, '' -> –
    s=(s or "").strip()
    if not s: return "–"
    try: return str(int(float(s)))
    except: return s

HAENG={'행정','직업상담','세무','관세','통계','감사','교정','보호','검찰','마약수사','출입국관리','철도경찰','외무영사'}
def gun(j): return '행정' if j in HAENG else '기술'

# ── 연도별 합계 ──
tot={y:{'sb':0,'cw':0,'eu':0,'hp':0} for y in Y}
for r in g9:
    y=r['연도']; tot[y]['sb']+=num(r['선발예정인원']); tot[y]['cw']+=num(r['접수인원'])
    tot[y]['eu']+=num(r['응시인원']); tot[y]['hp']+=num(r['필기합격인원'])
def comp(y): return f"{tot[y]['cw']/tot[y]['sb']:.1f}:1" if tot[y]['sb'] else "–"
def yul(y):  return f"{tot[y]['eu']/tot[y]['cw']*100:.0f}%" if tot[y]['cw'] else "–"

# ── 직렬별 4개년 선발 ──
jr=defaultdict(lambda:{y:0 for y in Y})
for r in g9: jr[r['직렬']][r['연도']]+=num(r['선발예정인원'])
jr_tot={k:sum(v.values()) for k,v in jr.items()}
top5=sorted(jr_tot,key=lambda x:-jr_tot[x])[:5]

# ── 직류(전국, 비권역) 4개년 합격선 + 2026 선발/경쟁률 ──
main={}
for r in g9:
    if r['임용예정기관']: continue
    dae=r['대상']
    if dae not in ('일반','남','여'): continue
    label=r['직류'].replace(' 전국','')+{'남':'(남)','여':'(여)'}.get(dae,'')  # 연도별 '세무'/'세무 전국' 등 병합
    key=(gun(r['직렬']), r['직렬'], label)
    e=main.setdefault(key,{y:'' for y in Y}); e.setdefault('sb','—'); e.setdefault('cp','—')
    e[r['연도']]=r['합격선']
    if r['연도']=='2026':
        e['sb']=r['선발예정인원'] or '—'; e['cp']=r['경쟁률(접수/선발)'] or '—'
# 대표 합격선(TOP5용): 직렬 내 2026 선발 최대 직류의 합격선들
def rep_cut(jik):
    cands=[(k,v) for k,v in main.items() if k[1]==jik]
    if not cands: return {y:'–' for y in Y}, ''
    cands.sort(key=lambda kv:-num(kv[1]['sb']))
    k,v=cands[0]; return v, k[2]

# ── 지역구분(권역) 2026 합격선 ──
region=defaultdict(list)  # 직류 -> [(권역,합격선)]
for r in g9:
    if r['임용예정기관'] and r['대상']=='일반' and r['연도']=='2026':
        region[r['직류']].append((r['임용예정기관'], cut(r['합격선'])))

# ===== HTML 빌드 =====
def extab_full(title, n, items):
    """items: list of (label, e-dict). 직류 | 선발 | 경쟁률 | 23 24 25 26"""
    h=[f'<div class="blk"><div class="mh"><span class="n mono">{n}</span><h3 class="serif">{title}</h3></div><div class="bd">']
    h.append('<table class="extab natab"><colgroup><col style="width:30mm"><col><col><col><col><col><col></colgroup>')
    h.append('<thead><tr><th>직류</th><th>선발</th><th>경쟁률</th><th>’23</th><th>’24</th><th>’25</th><th>’26</th></tr></thead><tbody>')
    for label,e in items:
        h.append(f'<tr><td>{label}</td><td>{e["sb"]}</td><td>{e["cp"]}</td>'
                 f'<td>{cut(e["2023"])}</td><td>{cut(e["2024"])}</td><td>{cut(e["2025"])}</td><td class="cut">{cut(e["2026"])}</td></tr>')
    h.append('</tbody></table></div></div>')
    return "\n".join(h)

def page(inner, folio, rh):
    return ('  <div class="spread"><div class="page">\n'
            f'    <div class="rhead"><span class="r">PART 1 · 국가직 9급</span><span>{rh}</span></div>\n'
            f'{inner}\n'
            f'    <div class="folio"><span class="src">국가직 9급 공채 필기 합격선</span><span class="pg serif">{folio}</span></div>\n'
            '  </div></div>')

# ── 페이지 1: 4개년 요약 ──
p1=['<div class="blk"><div class="mh"><span class="n mono">1-1</span><h3 class="serif">4개년 추이</h3><span class="flag real fb">실데이터</span></div><div class="bd">']
p1.append('<table class="extab fix"><colgroup><col style="width:26mm"><col><col><col><col></colgroup>')
p1.append('<caption>전 모집단위 합계 · 2023–2026</caption>')
p1.append('<thead><tr><th>구분</th><th>2023</th><th>2024</th><th>2025</th><th>2026</th></tr></thead><tbody>')
labels=[('선발예정','sb'),('출원(접수)','cw'),('응시','eu'),('필기합격','hp')]
for lab,k in labels:
    p1.append('<tr><td>'+lab+'</td>'+''.join(f'<td>{comma(tot[y][k])}</td>' for y in Y)+'</tr>')
p1.append('<tr><td>경쟁률</td>'+''.join(f'<td>{comp(y)}</td>' for y in Y)+'</tr>')
p1.append('<tr><td>응시율</td>'+''.join(f'<td>{yul(y)}</td>' for y in Y)+'</tr>')
p1.append('</tbody></table></div></div>')
p1.append('<div class="blk"><div class="mh"><span class="n mono">1-2</span><h3 class="serif">한눈에 — 특징</h3></div><div class="bd"><div class="howto" style="grid-template-columns:1fr 1fr">')
p1.append(f'<div class="ht"><div class="t">📉 선발은 줄고, 경쟁은 세지고</div><ul><li><b>·</b>선발 <strong>5,326 → 3,802명</strong> (4년간 −29%)</li><li><b>·</b>경쟁률 <strong>{comp("2023")} → {comp("2026")}</strong></li><li><b>·</b>응시율 75~78% 유지</li></ul></div>')
p1.append('<div class="ht"><div class="t">🧩 모집 구성</div><ul><li><b>·</b><strong>일반</strong> + 장애인 + 저소득 구분모집</li><li><b>·</b><strong>지역구분모집</strong> — 일반행정·우정 권역별 선발</li><li><b>·</b>합격선 기준 = <strong>과목평균</strong>(100점)</li></ul></div>')
p1.append('</div>')
p1.append('<p style="margin-top:2mm;font-size:var(--fs-sm)">선발 규모 1~5위: <strong>'+' · '.join(top5)+'</strong> (이 다섯 직렬이 4개년 선발의 대부분).</p>')
p1.append('</div></div>')

# ── 페이지 2: TOP 5 직렬 ──
p2=['<div class="blk"><div class="mh"><span class="n mono">1-3</span><h3 class="serif">TOP 5 직렬 — 선발 규모</h3></div><div class="bd">']
p2.append('<table class="extab natab"><colgroup><col style="width:20mm"><col><col><col><col><col style="width:30mm"></colgroup>')
p2.append('<caption>4개년 선발인원 · 대표 직류 합격선(’26)</caption>')
p2.append('<thead><tr><th>직렬</th><th>’23</th><th>’24</th><th>’25</th><th>’26</th><th>대표 직류 · 합격선’26</th></tr></thead><tbody>')
for jik in top5:
    v,lab=rep_cut(jik)
    p2.append(f'<tr><td><strong>{jik}</strong></td>'+''.join(f'<td>{int(jr[jik][y])}</td>' for y in Y)
              +f'<td style="text-align:left">{lab} <span class="cut">{cut(v["2026"])}</span></td></tr>')
p2.append('</tbody></table>')
p2.append('<p style="margin-top:1.5mm;font-size:var(--fs-xs);color:var(--muted)">※ 선발인원=전 대상 합계. 대표 직류=직렬 내 2026 선발 최다 직류(일반 기준).</p></div></div>')
# TOP5 보조: 대표 직류 4개년 합격선 흐름
p2.append('<div class="blk"><div class="mh"><span class="n mono">1-4</span><h3 class="serif">대표 직류 합격선 4개년</h3></div><div class="bd">')
p2.append('<table class="extab natab"><colgroup><col style="width:38mm"><col><col><col><col></colgroup>')
p2.append('<thead><tr><th>대표 직류</th><th>’23</th><th>’24</th><th>’25</th><th>’26</th></tr></thead><tbody>')
for jik in top5:
    v,lab=rep_cut(jik)
    p2.append(f'<tr><td>{jik} · {lab}</td><td>{cut(v["2023"])}</td><td>{cut(v["2024"])}</td><td>{cut(v["2025"])}</td><td class="cut">{cut(v["2026"])}</td></tr>')
p2.append('</tbody></table></div></div>')

# ── 페이지 3·4: 전체 직류 ──
def items_of(gn):
    out=[(k[2],v) for k,v in main.items() if k[0]==gn]
    out.sort(key=lambda lv:-num(lv[1]['sb']))
    return out
p3=extab_full("전체 직류 합격선 — 행정직군", "1-5", items_of('행정'))
p4=[extab_full("전체 직류 합격선 — 기술직군", "1-6", items_of('기술'))]
# 지역구분
p4.append('<div class="blk"><div class="mh"><span class="n mono">1-7</span><h3 class="serif">지역구분모집 — 2026 권역별 합격선</h3></div><div class="bd">')
for jr_name in ['일반행정 지역','우정사업본부 지역']:
    if jr_name in region:
        chips=' '.join(f'<span class="rgcut">{rg} <b>{c}</b></span>' for rg,c in region[jr_name])
        p4.append(f'<div class="rgblk"><div class="rgh">{jr_name}</div><div class="rgrow">{chips}</div></div>')
p4.append('</div></div>')

PAGES=[page("\n".join(p1),"12","4개년 요약"),
       page("\n".join(p2),"13","TOP 5 직렬"),
       page(p3,"14","전체 직류 · 행정"),
       page("\n".join(p4),"15","전체 직류 · 기술")]

DOC='''<!DOCTYPE html>
<html lang="ko"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>포켓북 — PART 1 국가직 9급</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin><link rel="stylesheet" href="pocketbook.css"></head>
<body>
<div class="toolbar"><div><b>합격선 포켓북</b> · PART 1 국가직 9급 <span class="meta">— 4개년·TOP5·전체</span></div>
<div class="btns"><button class="b-print" onclick="window.print()">🖨 인쇄 / PDF</button></div></div>
<div class="fitwrap"><div class="deck" id="deck">
<!-- SPREADS:START -->
'''+"\n".join(PAGES)+'''
<!-- SPREADS:END -->
</div></div><script src="pocketbook.js"></script></body></html>'''
open(os.path.join(D,"포켓북_02_국가직9급.html"),"w",encoding="utf-8").write(DOC)
print("생성: 포켓북_02_국가직9급.html | 4쪽")
print("행정직군 직류수:", len(items_of('행정')), "/ 기술직군:", len(items_of('기술')))
