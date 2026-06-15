# -*- coding: utf-8 -*-
"""검증_data.csv → 국가직 7급(PART 2) 본문.
구성: ①3개년 추이(1·2차) ②합격선·경쟁률 랭킹 ③~ 직류별 카드(선발·출원·경쟁·응시·1차PSAT·2차전공 × 3개년)
7급은 1차 PSAT로 거르고 2차 전공이 최종 관문. 직류별로 연도별 지표 전부 제공. 톤 반반."""
import csv, os
from collections import defaultdict
D=os.path.dirname(__file__)
rows=list(csv.DictReader(open(os.path.join(D,"검증_data.csv"),encoding="utf-8-sig")))
YS=["2023","2024","2025"]
def num(s):
    s=(s or "").replace(",","").strip()
    try:return float(s)
    except:return 0
def comma(n):
    n=num(n) if isinstance(n,str) else n
    return f"{int(round(n)):,}" if n else "–"
def cutf(s):
    s=(s or "").strip()
    if not s:return "–"
    try:
        f=float(s)
        return str(int(f)) if f==int(f) else ("%.2f"%f).rstrip('0').rstrip('.')
    except:return s
def ratio(cw,sb):
    cw,sb=num(cw),num(sb)
    return f"{cw/sb:.1f}" if sb else "–"
HAENG={'행정','직업상담','세무','관세','통계','감사','교정','보호','검찰','마약수사','출입국관리','철도경찰','외무영사'}
def gun(j):return '행정직군' if j in HAENG else '기술직군'

g7=[r for r in rows if r["지역"]=="국가직" and r["직급"]=="7급"]
# 연도×회차 합계
TOT={y:{} for y in YS}
for y in YS:
    for hc,tag in [("1차-PSAT","1"),("2차-전공","2")]:
        rs=[r for r in g7 if r['연도']==y and r['회차']==hc]
        TOT[y][tag]={'sb':sum(num(r['선발예정인원']) for r in rs),'cw':sum(num(r['접수인원']) for r in rs),
                     'eu':sum(num(r['응시인원']) for r in rs),'hp':sum(num(r['필기합격인원']) for r in rs)}
def comp(y):
    a=TOT[y]['1'];return f"{a['cw']/a['sb']:.1f}:1" if a['sb'] else "–"

# 직류 카드(일반)
cards=defaultdict(lambda:{y:{} for y in YS})
for r in g7:
    if r['대상']!='일반':continue
    key=(gun(r['직렬']),r['직렬'],r['직류'].replace(' 전국',''))  # 연도별 '일반행정 전국'↔'일반행정' 병합
    e=cards[key][r['연도']]
    e['sb']=r['선발예정인원'];e['cw']=r['접수인원']
    if r['회차']=='1차-PSAT': e['eu1']=r['응시인원']; e['cut1']=r['합격선']
    else: e['eu2']=r['응시인원']; e['cut2']=r['합격선']
def sb25(k):return num((cards[k]['2025'] or {}).get('sb',0))
def cards_of(gn):
    ks=[k for k in cards if k[0]==gn]; ks.sort(key=lambda k:-sb25(k)); return ks

# 랭킹(2025): 2차 전공 합격선, 경쟁률
rk=[]
for k in cards:
    e=cards[k]['2025']
    if not e:continue
    rk.append((k[2],num(e.get('cut2',0)),num(e.get('cw',0))/num(e.get('sb',1)) if num(e.get('sb',0)) else 0,e.get('cut2','')))
cut_rk=[x for x in rk if x[1]>0]
cut_hi=sorted(cut_rk,key=lambda x:-x[1])[:8]; cut_lo=sorted(cut_rk,key=lambda x:x[1])[:8]
cmp_hi=sorted([x for x in rk if x[2]>0],key=lambda x:-x[2])[:8]; cmp_lo=sorted([x for x in rk if x[2]>0],key=lambda x:x[2])[:8]

def page(inner,folio,rh):
    return ('  <div class="spread"><div class="page">\n'
            f'    <div class="rhead"><span class="r">PART 2 · 국가직 7급</span><span>{rh}</span></div>\n{inner}\n'
            f'    <div class="folio"><span class="src">국가직 7급 공채 필기 합격선</span><span class="pg serif">{folio}</span></div>\n  </div></div>')
def blk(n,title,body,flag=""):
    return f'<div class="blk"><div class="mh"><span class="n mono">{n}</span><h3 class="serif">{title}</h3>{flag}</div><div class="bd">{body}</div></div>'

# 페이지1: 3개년 추이
t='<table class="extab fix"><colgroup><col style="width:30mm"><col><col><col></colgroup><caption>전 모집단위 합계 · 1차 PSAT / 2차 전공</caption>'
t+='<thead><tr><th>구분</th>'+''.join(f'<th>{y}</th>' for y in YS)+'</tr></thead><tbody>'
t+='<tr><td>선발</td>'+''.join(f'<td>{comma(TOT[y]["1"]["sb"])}</td>' for y in YS)+'</tr>'
t+='<tr><td>출원</td>'+''.join(f'<td>{comma(TOT[y]["1"]["cw"])}</td>' for y in YS)+'</tr>'
t+='<tr><td>경쟁률</td>'+''.join(f'<td>{comp(y)}</td>' for y in YS)+'</tr>'
t+='<tr><td>1차 응시</td>'+''.join(f'<td>{comma(TOT[y]["1"]["eu"])}</td>' for y in YS)+'</tr>'
t+='<tr><td>1차 합격</td>'+''.join(f'<td>{comma(TOT[y]["1"]["hp"])}</td>' for y in YS)+'</tr>'
t+='<tr><td>2차 응시</td>'+''.join(f'<td>{comma(TOT[y]["2"]["eu"])}</td>' for y in YS)+'</tr>'
t+='<tr><td>최종 필기합격</td>'+''.join(f'<td>{comma(TOT[y]["2"]["hp"])}</td>' for y in YS)+'</tr></tbody></table>'
ins='<div class="howto" style="grid-template-columns:1fr 1fr"><div class="ht"><div class="t">🪜 2단계 시험</div><ul><li><b>·</b><strong>1차 PSAT</strong>로 거르고 → <strong>2차 전공</strong>이 최종</li><li><b>·</b>출원 ~2.6만 → 1차 응시 ~1.6만 → 2차 ~3.9천 → 최종 ~700</li></ul></div><div class="ht"><div class="t">📌 합격선</div><ul><li><b>·</b>1차=PSAT 평균, 2차=전공 평균 (둘 다 100점)</li><li><b>·</b>9급보다 선발 적고(연 600~720) 경쟁 치열</li></ul></div></div>'
P1=blk("2-1","3개년 추이",t,'<span class="flag real fb">실데이터</span>')+blk("2-2","7급은 이렇게 본다",ins)

# 페이지2: 랭킹
def ranklist(title,items,kind):
    h=[f'<div class="rankbox"><div class="rkh">{title}</div>']
    for i,(lab,c,cp,raw) in enumerate(items,1):
        v=(cutf(raw) if kind=='cut' else f'{cp:.0f}:1'); cls=' cut' if kind=='cut' else ''
        h.append(f'<div class="rkrow"><span class="rkn">{i}</span><span class="rkl">{lab}</span><span class="rkv{cls}">{v}</span></div>')
    return "".join(h)+'</div>'
r_cut=f'<div class="rankwrap">{ranklist("2차(전공) 합격선 높은 TOP 8",cut_hi,"cut")}{ranklist("2차 합격선 낮은 BOTTOM 8",cut_lo,"cut")}</div>'
r_cmp=f'<div class="rankwrap">{ranklist("경쟁률 높은 TOP 8",cmp_hi,"cmp")}{ranklist("경쟁률 낮은 BOTTOM 8",cmp_lo,"cmp")}</div>'
P2=blk("2-3","2차(전공) 합격선 랭킹 (2025)",r_cut+'<p style="margin-top:1.5mm;font-size:var(--fs-xs);color:var(--muted)">※ 합격선=과목평균 100점. 검찰·인사조직이 높은 편.</p>')+blk("2-4","경쟁률 랭킹 (2025)",r_cmp)

# 페이지3~: 직류 카드
def card(k):
    gn,jik,lab=k; d=cards[k]
    h=[f'<div class="dcard"><div class="dch"><span class="nm">{lab}</span><span class="jg">{jik}</span></div>']
    h.append('<table><thead><tr><th></th>'+''.join(f'<th>’{y[2:]}</th>' for y in YS)+'</tr></thead><tbody>')
    def r(name,fn,cls=''):
        return f'<tr class="{cls}"><td>{name}</td>'+''.join(f'<td>{fn(d[y])}</td>' for y in YS)+'</tr>'
    h.append(r('선발',lambda e:comma(e['sb']) if e else '–'))
    h.append(r('출원',lambda e:comma(e['cw']) if e else '–'))
    h.append(r('경쟁',lambda e:ratio(e['cw'],e['sb']) if e else '–'))
    h.append(r('1차응시',lambda e:comma(e.get('eu1')) if e else '–'))
    h.append(r('1차 PSAT',lambda e:cutf(e.get('cut1','')) if e else '–','cut1row'))
    h.append(r('2차 전공',lambda e:cutf(e.get('cut2','')) if e else '–','cutrow'))
    h.append('</tbody></table></div>')
    return "".join(h)
def cardpage(ks,n,title):
    return blk(n,title,'<div class="cardgrid">'+''.join(card(k) for k in ks)+'</div>')
def chunk(l,s):return [l[i:i+s] for i in range(0,len(l),s)]
HA=cards_of('행정직군'); GI=cards_of('기술직군')
_ha=chunk(HA,8); _gi=chunk(GI,8)
ha_pages=[cardpage(c,"2-5",f"직류별 상세 — 행정직군 ({i+1}/{len(_ha)})") for i,c in enumerate(_ha)]
gi_pages=[cardpage(c,"2-6",f"직류별 상세 — 기술직군 ({i+1}/{len(_gi)})") for i,c in enumerate(_gi)]

content=[("3개년 요약",P1),("합격선·경쟁률 랭킹",P2)]
for p in ha_pages: content.append(("직류 상세·행정",p))
for p in gi_pages: content.append(("직류 상세·기술",p))
PAGES=[page(inner,str(21+i),rh) for i,(rh,inner) in enumerate(content)]

DOC='<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">'\
'<title>포켓북 — PART 2 국가직 7급</title><link rel="preconnect" href="https://fonts.googleapis.com">'\
'<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin>'\
'<link rel="stylesheet" href="pocketbook.css"></head><body>'\
'<div class="toolbar"><div><b>합격선 포켓북</b> · PART 2 국가직 7급</div>'\
'<div class="btns"><button class="b-print" onclick="window.print()">🖨 인쇄 / PDF</button></div></div>'\
'<div class="fitwrap"><div class="deck" id="deck">\n<!-- SPREADS:START -->\n'+"\n".join(PAGES)+'\n<!-- SPREADS:END -->\n'\
'</div></div><script src="pocketbook.js"></script></body></html>'
open(os.path.join(D,"포켓북_03_국가직7급.html"),"w",encoding="utf-8").write(DOC)
print("생성: 포켓북_03_국가직7급.html | 페이지",len(PAGES),"| 행정",len(HA),"기술",len(GI))
