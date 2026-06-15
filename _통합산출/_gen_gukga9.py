# -*- coding: utf-8 -*-
"""검증_data.csv → 국가직 9급(PART 1) 본문.
구성: ①큰그림 ②국가직vs지방직 ③합격선·경쟁률 랭킹 ④~ 직류별 카드(5지표×4개년) ⑤지역구분 권역별
톤: 반반(표+인사이트). 직류별로 연도별 선발·출원·응시·경쟁률·합격선 전부 제공."""
import csv, os
from collections import defaultdict
D=os.path.dirname(__file__)
rows=list(csv.DictReader(open(os.path.join(D,"검증_data.csv"),encoding="utf-8-sig")))
Y=["2023","2024","2025","2026"]
def num(s):
    s=(s or "").replace(",","").strip()
    try:return float(s)
    except:return 0
def comma(n):
    n=num(n) if isinstance(n,str) else n
    return f"{int(round(n)):,}" if n else "–"
def cut(s):
    s=(s or "").strip()
    if not s:return "–"
    try:return str(int(float(s)))
    except:return s
def ratio(cw,sb):
    cw,sb=num(cw),num(sb)
    return f"{cw/sb:.1f}" if sb else "–"
HAENG={'행정','직업상담','세무','관세','통계','감사','교정','보호','검찰','마약수사','출입국관리','철도경찰','외무영사'}
def gun(j):return '행정직군' if j in HAENG else '기술직군'

g9=[r for r in rows if r["지역"]=="국가직" and r["직급"]=="9급"]
# 지방직 9급(전국 합계용)
jb9=[r for r in rows if r["지역"]!="국가직" and r["시험종류"]=="공무원" and r["직급"]=="9급"]

# ── 연도별 합계 ──
def totals(data):
    t={y:{'sb':0,'cw':0,'eu':0,'hp':0} for y in Y}
    for r in data:
        y=r['연도']
        if y not in t:continue
        t[y]['sb']+=num(r['선발예정인원']);t[y]['cw']+=num(r['접수인원'])
        t[y]['eu']+=num(r['응시인원']);t[y]['hp']+=num(r['필기합격인원'])
    return t
T=totals(g9); JB=totals(jb9)
def comp(t,y):return f"{t[y]['cw']/t[y]['sb']:.1f}:1" if t[y]['sb'] else "–"
def yul(t,y): return f"{t[y]['eu']/t[y]['cw']*100:.0f}%" if t[y]['cw'] else "–"

# ── 직류 카드 데이터(비권역, 일반/남/여) ──
cards=defaultdict(lambda:{y:None for y in Y})
for r in g9:
    if r['임용예정기관']:continue
    if r['대상'] not in ('일반','남','여'):continue
    lab=r['직류'].replace(' 전국','')+{'남':'(남)','여':'(여)'}.get(r['대상'],'')
    cards[(gun(r['직렬']),r['직렬'],lab)][r['연도']]={'sb':r['선발예정인원'],'cw':r['접수인원'],'eu':r['응시인원'],'cut':r['합격선']}
def card_sb26(k):
    d=cards[k]['2026'];return num(d['sb']) if d else 0
def cards_of(gn):
    ks=[k for k in cards if k[0]==gn]
    ks.sort(key=lambda k:-card_sb26(k))
    return ks

# ── 랭킹(2026 일반/남/여 비권역) ──
rk=[]
for k in cards:
    d=cards[k]['2026']
    if not d:continue
    c=num(d['cut']); cp=num(d['cw'])/num(d['sb']) if num(d['sb']) else 0
    rk.append((k[2],c,cp,num(d['sb']),num(d['cut'])>0))
cut_rk=[x for x in rk if x[4]]
cut_hi=sorted(cut_rk,key=lambda x:-x[1])[:8]
cut_lo=sorted(cut_rk,key=lambda x:x[1])[:8]
cmp_hi=sorted([x for x in rk if x[2]>0],key=lambda x:-x[2])[:8]
cmp_lo=sorted([x for x in rk if x[2]>0],key=lambda x:x[2])[:8]

# ===== 빌드 =====
def page(inner,folio,rh):
    return ('  <div class="spread"><div class="page">\n'
            f'    <div class="rhead"><span class="r">PART 1 · 국가직 9급</span><span>{rh}</span></div>\n{inner}\n'
            f'    <div class="folio"><span class="src">국가직 9급 공채 필기 합격선</span><span class="pg serif">{folio}</span></div>\n  </div></div>')
def blk(n,title,body,flag=""):
    return f'<div class="blk"><div class="mh"><span class="n mono">{n}</span><h3 class="serif">{title}</h3>{flag}</div><div class="bd">{body}</div></div>'

# 페이지1: 큰그림
t1='<table class="extab fix"><colgroup><col style="width:24mm"><col><col><col><col></colgroup><caption>전 모집단위 합계</caption>'
t1+='<thead><tr><th>구분</th>'+''.join(f'<th>{y}</th>' for y in Y)+'</tr></thead><tbody>'
for lab,kk in [('선발','sb'),('출원','cw'),('응시','eu'),('필기합격','hp')]:
    t1+='<tr><td>'+lab+'</td>'+''.join(f'<td>{comma(T[y][kk])}</td>' for y in Y)+'</tr>'
t1+='<tr><td>경쟁률</td>'+''.join(f'<td>{comp(T,y)}</td>' for y in Y)+'</tr>'
t1+='<tr><td>응시율</td>'+''.join(f'<td>{yul(T,y)}</td>' for y in Y)+'</tr></tbody></table>'
ins1='<div class="howto" style="grid-template-columns:1fr 1fr"><div class="ht"><div class="t">📉 선발 줄고, 경쟁 세짐</div><ul><li><b>·</b>선발 <strong>5,326→3,802</strong> (−29%)</li><li><b>·</b>경쟁률 <strong>22.8→28.6:1</strong></li></ul></div><div class="ht"><div class="t">🧩 모집 구성</div><ul><li><b>·</b>일반+장애+저소득 · <strong>지역구분모집</strong></li><li><b>·</b>합격선=<strong>과목평균</strong>(100점)</li></ul></div></div>'
P1=blk("1-1","4개년 추이",t1,'<span class="flag real fb">실데이터</span>')+blk("1-2","한눈에",ins1)

# 페이지2: 국가직 vs 지방직 9급
def crow(lab,t,y):
    return f'<td>{lab}</td><td>{comma(t[y]["sb"])}</td><td>{comp(t,y)}</td>'
c2='<table class="extab natab"><colgroup><col style="width:20mm"><col><col><col><col></colgroup>'
c2+='<thead><tr><th>구분</th><th>국가직 선발</th><th>국가직 경쟁</th><th>지방직 선발</th><th>지방직 경쟁</th></tr></thead><tbody>'
for y in ["2023","2024","2025"]:
    c2+=f'<tr><td>{y}</td><td>{comma(T[y]["sb"])}</td><td>{comp(T,y)}</td><td>{comma(JB[y]["sb"])}</td><td>{comp(JB,y)}</td></tr>'
c2+='</tbody></table>'
ins2='<div class="howto" style="grid-template-columns:1fr"><div class="ht"><div class="t">⚖️ 한 줄 비교 (2025)</div><ul>'\
 f'<li><b>·</b>지방직이 <strong>약 {JB["2025"]["sb"]/T["2025"]["sb"]:.1f}배</strong> 더 뽑음 (지방 {comma(JB["2025"]["sb"])} vs 국가 {comma(T["2025"]["sb"])})</li>'\
 f'<li><b>·</b>대신 경쟁률은 국가직이 높음 (국가 {comp(T,"2025")} vs 지방 {comp(JB,"2025")})</li>'\
 '<li><b>·</b>국가직=전국 단일·이동 多 / 지방직=거주지·연고 중심</li></ul></div></div>'
P2=blk("1-3","국가직 vs 지방직 9급",c2,'<span class="flag real fb">실데이터</span>')+blk("1-4","무엇이 다른가",ins2)

# 페이지3: 랭킹
def ranklist(title,items,kind):
    h=[f'<div class="rankbox"><div class="rkh">{title}</div>']
    for i,(lab,c,cp,sb,_) in enumerate(items,1):
        v=(str(int(c)) if kind=='cut' else f'{cp:.0f}:1')
        cls=' cut' if kind=='cut' else ''
        h.append(f'<div class="rkrow"><span class="rkn">{i}</span><span class="rkl">{lab}</span><span class="rkv{cls}">{v}</span></div>')
    h.append('</div>')
    return "".join(h)
r_cut=f'<div class="rankwrap">{ranklist("합격선 높은 TOP 8",cut_hi,"cut")}{ranklist("합격선 낮은 BOTTOM 8",cut_lo,"cut")}</div>'
r_cmp=f'<div class="rankwrap">{ranklist("경쟁률 높은 TOP 8",cmp_hi,"cmp")}{ranklist("경쟁률 낮은 BOTTOM 8",cmp_lo,"cmp")}</div>'
P3=blk("1-5","합격선 랭킹 (2026)",r_cut+'<p style="margin-top:1.5mm;font-size:var(--fs-xs);color:var(--muted)">※ 합격선=과목평균 100점. 교육행정·전산이 높고, 세무·시설이 낮은 편.</p>')\
  +blk("1-6","경쟁률 랭킹 (2026)",r_cmp)

# 페이지4~: 직류 카드
def card(k):
    gn,jik,lab=k; d=cards[k]
    h=[f'<div class="dcard"><div class="dch"><span class="nm">{lab}</span><span class="jg">{jik}</span></div>']
    h.append('<table><thead><tr><th></th>'+''.join(f'<th>’{y[2:]}</th>' for y in Y)+'</tr></thead><tbody>')
    def row(name,key,fmt):
        cells=''.join(f'<td>{fmt(d[y][key]) if d[y] else "–"}</td>' for y in Y)
        return f'<tr><td>{name}</td>{cells}</tr>'
    h.append(row('선발','sb',comma))
    h.append(row('출원','cw',comma))
    h.append(row('응시','eu',comma))
    h.append('<tr><td>경쟁</td>'+''.join(f'<td>{ratio(d[y]["cw"],d[y]["sb"]) if d[y] else "–"}</td>' for y in Y)+'</tr>')
    h.append('<tr class="cutrow"><td>합격선</td>'+''.join(f'<td>{cut(d[y]["cut"]) if d[y] else "–"}</td>' for y in Y)+'</tr>')
    h.append('</tbody></table></div>')
    return "".join(h)
def cardpage(gn,ks,n,title):
    body='<div class="cardgrid">'+''.join(card(k) for k in ks)+'</div>'
    return blk(n,title,body)
HA=cards_of('행정직군'); GI=cards_of('기술직군')
# 행정직군 분할(카드 많음): 12개씩
def chunk(l,s):return [l[i:i+s] for i in range(0,len(l),s)]
_ha=chunk(HA,10); _gi=chunk(GI,10)
ha_pages=[cardpage('행정직군',c,"1-7",f"직류별 상세 — 행정직군 ({i+1}/{len(_ha)})") for i,c in enumerate(_ha)]
gi_pages=[cardpage('기술직군',c,"1-8",f"직류별 상세 — 기술직군 ({i+1}/{len(_gi)})") for i,c in enumerate(_gi)]

# 지역구분 권역별 (2026)
region=defaultdict(list)
for r in g9:
    if r['임용예정기관'] and r['대상']=='일반' and r['연도']=='2026':
        region[r['직류']].append((r['임용예정기관'],cut(r['합격선']),r['선발예정인원'],ratio(r['접수인원'],r['선발예정인원'])))
rg_body=[]
for nm in ['일반행정 지역','우정사업본부 지역']:
    if nm in region:
        chips=' '.join(f'<span class="rgcut">{rg} <b>{c}</b><span style="color:var(--muted);font-weight:400"> 선{sb}·{cp}:1</span></span>' for rg,c,sb,cp in region[nm])
        rg_body.append(f'<div class="rgblk"><div class="rgh">{nm}</div><div class="rgrow">{chips}</div></div>')
P_REGION=blk("1-9","지역구분모집 — 2026 권역별 (합격선·선발·경쟁)","".join(rg_body))

# 페이지 조립 + 폴리오(12부터)
content=[("4개년 요약",P1),("국가직 vs 지방직",P2),("합격선·경쟁률 랭킹",P3)]
for i,p in enumerate(ha_pages): content.append((f"직류 상세·행정",p))
for p in gi_pages: content.append(("직류 상세·기술",p))
content.append(("지역구분모집",P_REGION))
PAGES=[page(inner,str(12+i),rh) for i,(rh,inner) in enumerate(content)]

DOC='<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">'\
'<title>포켓북 — PART 1 국가직 9급</title><link rel="preconnect" href="https://fonts.googleapis.com">'\
'<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin>'\
'<link rel="stylesheet" href="pocketbook.css"></head><body>'\
'<div class="toolbar"><div><b>합격선 포켓북</b> · PART 1 국가직 9급</div>'\
'<div class="btns"><button class="b-print" onclick="window.print()">🖨 인쇄 / PDF</button></div></div>'\
'<div class="fitwrap"><div class="deck" id="deck">\n<!-- SPREADS:START -->\n'+"\n".join(PAGES)+'\n<!-- SPREADS:END -->\n'\
'</div></div><script src="pocketbook.js"></script></body></html>'
open(os.path.join(D,"포켓북_02_국가직9급.html"),"w",encoding="utf-8").write(DOC)
print("생성: 포켓북_02_국가직9급.html | 페이지", len(PAGES))
print("행정직군 직류", len(HA), "/ 기술직군", len(GI), "/ 랭킹 대상", len(rk))
