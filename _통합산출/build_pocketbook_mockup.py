# -*- coding: utf-8 -*-
"""검증_data.csv(실데이터)로 포켓북 개선 목업(A5 페이지뷰어) HTML 생성.
기존 목업의 디자인틀 + 제안 반영: 전국종합=합격선 범위(평균X), 양성평등/회차/단위/공개경쟁 명기, 7급=광역시 한정."""
import csv, statistics, html
from collections import defaultdict

CSV = '검증_data.csv'
OUT = '포켓북_목업_실데이터.html'
rows = list(csv.DictReader(open(CSV, encoding='utf-8-sig')))
def I(x):
    try: return int(str(x).replace(',', ''))
    except: return None
def F(x):
    try: return float(x)
    except: return None
G  = [r for r in rows if r['시험종류'] == '공무원']
GY = [r for r in rows if r['시험종류'] == '교행']
def med(v): return statistics.median(v)

# ---- 집계 ----
# 전국 종합 일반행정 일반 9급
nat = {}
for y in ('2023', '2024', '2025'):
    s = [r for r in G if r['연도']==y and r['직류']=='일반행정' and r['직급']=='9급' and r['대상']=='일반']
    sel = sum(I(r['선발예정인원']) or 0 for r in s); app = sum(I(r['접수인원']) or 0 for r in s); ex = sum(I(r['응시인원']) or 0 for r in s)
    c = sorted(F(r['합격선']) for r in s if F(r['합격선']) is not None)
    nat[y] = dict(n=len(s), sel=sel, app=app, ex=ex, comp=round(app/sel,1) if sel else 0,
                  rate=round(ex/app*100) if app else 0, cmin=int(c[0]), cmed=round(med(c)), cmax=int(c[-1]))

# 서울 2025 직렬별
seoul = defaultdict(lambda: [0,0,[]])
for r in G:
    if r['지역']=='서울' and r['연도']=='2025' and r['직급']=='9급' and r['대상']=='일반':
        seoul[r['직류']][0]+=I(r['선발예정인원']) or 0; seoul[r['직류']][1]+=I(r['접수인원']) or 0
        if F(r['합격선']) is not None: seoul[r['직류']][2].append(F(r['합격선']))
seoul25 = []
for k,(sl,ap,ct) in sorted(seoul.items(), key=lambda x:-x[1][0])[:6]:
    seoul25.append((k, sl, ap, round(ap/sl,1) if sl else 0, round(med(ct)) if ct else None))

# 직렬별 전국 2025 범위
jr = defaultdict(lambda:[0,[]])
for r in G:
    if r['연도']=='2025' and r['직급']=='9급' and r['대상']=='일반':
        jr[r['직류']][0]+=I(r['선발예정인원']) or 0
        if F(r['합격선']) is not None: jr[r['직류']][1].append(F(r['합격선']))
jr_nat = []
for k,(sl,ct) in sorted(jr.items(), key=lambda x:-x[1][0])[:6]:
    if ct: jr_nat.append((k, sl, int(min(ct)), int(max(ct)), round(med(ct))))

# 시도 랭킹 2025 일반행정(중앙+범위)
reg = defaultdict(list)
for r in G:
    if r['연도']=='2025' and r['직류']=='일반행정' and r['직급']=='9급' and r['대상']=='일반' and F(r['합격선']) is not None:
        reg[r['지역']].append(F(r['합격선']))
rank = sorted(((round(med(v)), int(min(v)), int(max(v)), k, len(v)) for k,v in reg.items()), reverse=True)

# 교행 전국 종합(총점)
gyo = {}
for y in ('2023','2024','2025'):
    s = [r for r in GY if r['연도']==y and r['직류']=='교육행정' and r['대상']=='일반']
    sel=sum(I(r['선발예정인원']) or 0 for r in s); app=sum(I(r['접수인원']) or 0 for r in s); ex=sum(I(r['응시인원']) or 0 for r in s)
    c=sorted(F(r['합격선']) for r in s if F(r['합격선']) is not None)
    gyo[y]=dict(n=len(s),sel=sel,app=app,comp=round(app/sel,1) if sel else 0,
                rate=round(ex/app*100) if app else 0, cmin=int(c[0]),cmed=round(med(c)),cmax=int(c[-1]))

# 양성평등
yp = [r for r in rows if r['양성평등합격선'].strip() and F(r['합격선']) is not None and F(r['양성평등합격선']) is not None]
yp_n = len(yp)
yp_samp = []
seen=set()
for r in yp:
    key=(r['지역'],r['직류'])
    if r['시험종류']=='공무원' and key not in seen and F(r['합격선'])>F(r['양성평등합격선']):
        seen.add(key); yp_samp.append((r['지역'],r['연도'],r['직류'],int(F(r['합격선'])),int(F(r['양성평등합격선']))))
    if len(yp_samp)>=5: break

# 서울 7급
s7 = [r for r in rows if r['직급']=='7급' and r['지역']=='서울' and r['대상']=='일반']
s7r = []
for r in sorted(s7, key=lambda x:-(I(x['선발예정인원']) or 0))[:5]:
    s7r.append((r['연도'], r['직류'], I(r['선발예정인원']), I(r['접수인원']), F(r['합격선']) and int(F(r['합격선']))))
metro7 = sorted(set(r['지역'] for r in rows if r['직급']=='7급'))

# ===================== HTML =====================
def rng_bar(mn, med_, mx, lo=40, hi=100):
    """min~median~max 범위 띠 (40~100 스케일)"""
    sp=hi-lo
    a=(mn-lo)/sp*100; b=(mx-lo)/sp*100; m=(med_-lo)/sp*100
    return (f'<div class="rb"><div class="rb-track"><div class="rb-span" style="left:{a:.0f}%;width:{b-a:.0f}%"></div>'
            f'<div class="rb-med" style="left:{m:.0f}%"><span>{med_}</span></div>'
            f'<div class="rb-lo" style="left:{a:.0f}%">{mn}</div><div class="rb-hi" style="left:{b:.0f}%">{mx}</div></div></div>')

def cells_nat(d):
    return (f"<tr><td>{{y}}</td><td>{d['sel']:,}</td><td>{d['app']:,}</td><td>{d['comp']}</td>"
            f"<td class='cut'>{d['cmed']}</td><td class='rngcell'>{d['cmin']}~{d['cmax']}</td></tr>")

PAGES = []

# 1 목차
PAGES.append(f'''<div class="page active">
 <div class="rhead"><span>POCKET BOOK</span><span class="r">CONTENTS</span></div>
 <div class="toc-kick mono">2023 — 2026 · 실데이터 기반</div>
 <div class="toc-h serif">목차</div>
 <div class="toc-grp"><span class="toc-pn mono">PART 0</span><div class="toc-pt serif">길잡이</div>
  <div class="toc-row"><span class="lbl">일러두기 · 용어 / 3대 기준</span><span class="dots"></span><span class="num">06</span></div>
  <div class="toc-row"><span class="lbl">4개년 핵심 요약</span><span class="dots"></span><span class="num">08</span></div></div>
 <div class="toc-grp"><span class="toc-pn mono">PART 1</span><div class="toc-pt serif">지방직 9급 공무원</div>
  <div class="toc-row"><span class="lbl">전국 종합(합격선 <b>범위</b>)</span><span class="dots"></span><span class="num">12</span></div>
  <div class="toc-row"><span class="lbl">시도별 상세 (17개 시도)</span><span class="dots"></span><span class="num">16</span></div>
  <div class="toc-row"><span class="lbl">직렬별 / 양성평등 합격선</span><span class="dots"></span><span class="num">40</span></div></div>
 <div class="toc-grp"><span class="toc-pn mono">PART 2</span><div class="toc-pt serif">지방직 7급 <span style="font-size:.7rem;color:var(--gold)">— 주요 광역시 한정</span></div>
  <div class="toc-row"><span class="lbl">서울·부산·대구·인천·광주</span><span class="dots"></span><span class="num">46</span></div></div>
 <div class="toc-grp"><span class="toc-pn mono">PART 3</span><div class="toc-pt serif">지방교육행정직 (교육청 9급)</div>
  <div class="toc-row"><span class="lbl">전국 종합 / 시도교육청별 (총점)</span><span class="dots"></span><span class="num">54</span></div></div>
 <div class="toc-grp"><span class="toc-pn mono">PART 4</span><div class="toc-pt serif">비교 · 분석</div>
  <div class="toc-row"><span class="lbl">시도 합격선 랭킹(범위)</span><span class="dots"></span><span class="num">70</span></div></div>
 <div class="folio"><span class="src"></span><span class="pg serif">4</span></div></div>''')

# 2 일러두기 + 3대 기준
PAGES.append('''<div class="page">
 <div class="rhead"><span class="r">PART 0 · 길잡이</span><span>0-1 일러두기</span></div>
 <div class="ptitle serif">용어 정의 & 3대 기준</div>
 <div class="psub">이 책의 모든 표는 아래 기준으로 작성되었습니다.</div>
 <dl>
  <div class="term"><dt>선발 / 출원 / 응시</dt><dd>선발예정·원서접수·실제응시 인원.</dd></div>
  <div class="term"><dt>경쟁률 <span class="en">RATIO</span></dt><dd>출원 ÷ 선발. <span class="f">(예: 11.8 : 1)</span></dd></div>
  <div class="term"><dt>합격선 <span class="en">CUT-OFF</span></dt><dd>필기합격 마지막 점수. <span class="f">가산점 미반영.</span></dd></div>
  <div class="term"><dt>양성평등 합격선</dt><dd>양성평등채용목표제 적용 시 별도 합격선.</dd></div>
 </dl>
 <div class="krit">
  <div class="kr"><b>① 공개경쟁만</b> 수록 — 경력경쟁(운전·시설관리·조리 등) 제외</div>
  <div class="kr"><b>② 회차 주의</b> — 지역마다 회차 상이(서울 1~3회, 제주 3·4회 등). 표는 연도 기준</div>
  <div class="kr"><b>③ 단위 다름</b> — 공무원=<b>과목평균</b>(100점), 교행=<b>총점</b>(500점)</div>
 </div>
 <div class="folio"><span class="src">※ 실데이터: 검증_data.csv 8,664행(2023~2025)</span><span class="pg serif">6</span></div></div>''')

# 3 핵심요약 (전국 일반행정 합격선 범위 추이 — 실데이터)
PAGES.append(f'''<div class="page">
 <div class="rhead"><span class="r">PART 0 · 길잡이</span><span>0-4 핵심 요약</span></div>
 <div class="ptitle serif">4개년 핵심 요약</div>
 <div class="psub">지방직 9급 일반행정 · 전국 합산 (실데이터)</div>
 <div class="big-stats">
  <div class="bstat"><div class="k">2025 합격선 범위</div><div class="v">{nat['2025']['cmin']}~{nat['2025']['cmax']}<small>점</small></div><div class="d mono">중앙 {nat['2025']['cmed']}점</div></div>
  <div class="bstat"><div class="k">2025 경쟁률</div><div class="v">{nat['2025']['comp']}<small> : 1</small></div><div class="d down mono">{nat['2023']['comp']} → {nat['2025']['comp']}</div></div>
  <div class="bstat"><div class="k">2025 선발</div><div class="v">{nat['2025']['sel']:,}<small>명</small></div><div class="d mono">{nat['2025']['n']}개 모집단위</div></div>
  <div class="bstat"><div class="k">2025 응시율</div><div class="v up">{nat['2025']['rate']}<small>%</small></div><div class="d mono">출원 {nat['2025']['app']:,}</div></div>
 </div>
 <div class="trend"><div class="tt"><span>합격선 중앙값 추이</span><b>단위: 점</b></div>
  <div class="bars">
   <div class="bar"><div class="col" style="height:{nat['2023']['cmed']}%"><span class="v">{nat['2023']['cmed']}</span></div><span class="yr">2023</span></div>
   <div class="bar"><div class="col" style="height:{nat['2024']['cmed']}%"><span class="v">{nat['2024']['cmed']}</span></div><span class="yr">2024</span></div>
   <div class="bar"><div class="col" style="height:{nat['2025']['cmed']}%"><span class="v">{nat['2025']['cmed']}</span></div><span class="yr">2025</span></div>
   <div class="bar future"><div class="col" style="height:50%"></div><span class="yr">2026</span></div></div></div>
 <div class="note-box" style="margin-top:14px;"><div class="nt mono">읽는 법</div>
  <p>전국 일반행정 합격선은 <b>단일값이 아니라 {nat['2025']['cmin']}~{nat['2025']['cmax']}점 범위</b>입니다(지역·시군별). "전국 평균"만 보지 말고 내 지역 페이지를 확인하세요.</p></div>
 <div class="folio"><span class="src">출처: 지자체 공고 · 실집계</span><span class="pg serif">8</span></div></div>''')

# 4 PART1 도비라
PAGES.append('''<div class="page divider"><div class="dn mono">PART 1</div><h2 class="serif">지방직 9급</h2>
 <div class="dl"></div><p class="dd">전국 종합부터 17개 시도 · 직렬 · 양성평등까지.</p>
 <div class="dcontents">전국 종합 · · · 12<br>시도별 · · · · · 16<br>직렬 / 양성평등 · 40</div></div>''')

# 5 전국 종합 (핵심 개선: 범위)
rows_nat = ''.join(cells_nat(nat[y]).format(y=y) for y in ('2023','2024','2025'))
rows_nat += f"<tr><td>2026</td><td class='tba'>예정</td><td class='tba'>—</td><td class='tba'>—</td><td class='tba'>—</td><td class='tba'>6.20 시행</td></tr>"
PAGES.append(f'''<div class="page">
 <div class="rhead"><span class="r">PART 1 · 지방직 9급</span><span>1-1 전국 종합</span></div>
 <div class="ptitle serif">전국 종합 · 일반행정</div>
 <div class="psub">전국 합산 · 합격선은 <b style="color:var(--red)">평균이 아닌 범위</b>로 표기</div>
 <table class="dt"><thead><tr><th>연도</th><th>선발</th><th>출원</th><th>경쟁</th><th>중앙</th><th>합격선범위</th></tr></thead>
  <tbody>{rows_nat}</tbody></table>
 <div class="rbwrap"><div class="tt2">합격선 분포 (최저 — 중앙 — 최고)</div>
  {rng_bar(nat['2023']['cmin'],nat['2023']['cmed'],nat['2023']['cmax'])}<div class="ryr">2023</div>
  {rng_bar(nat['2024']['cmin'],nat['2024']['cmed'],nat['2024']['cmax'])}<div class="ryr">2024</div>
  {rng_bar(nat['2025']['cmin'],nat['2025']['cmed'],nat['2025']['cmax'])}<div class="ryr">2025</div>
 </div>
 <div class="folio"><span class="src">※ 단일 "전국 합격선"은 존재하지 않음 · 실데이터</span><span class="pg serif">12</span></div></div>''')

# 6 서울 시도별
srows = ''.join(f"<tr><td>{k}</td><td>{sl:,}</td><td>{ap:,}</td><td>{cp}</td><td class='cut'>{cm if cm is not None else '-'}</td></tr>" for k,sl,ap,cp,cm in seoul25)
PAGES.append(f'''<div class="page">
 <div class="rhead"><span class="r">PART 1 · 지방직 9급</span><span>1-2 시도별 · 서울</span></div>
 <div class="ptitle serif">서울특별시</div>
 <div class="psub">직렬별 · 2025년 · 합격선=중앙값</div>
 <table class="dt"><thead><tr><th>직렬</th><th>선발</th><th>출원</th><th>경쟁</th><th>합격선</th></tr></thead>
  <tbody>{srows}</tbody></table>
 <div class="note-box" style="margin-top:14px;"><div class="nt mono">서울은 단일시험</div>
  <p>서울·부산 등 광역시는 시 전체가 한 시험이라 직렬당 합격선이 1개. <b>도(道) 지역은 시·군마다 달라</b> 범위로 봅니다(다음 장 랭킹 참고).</p></div>
 <div class="folio"><span class="src">※ 가산점 미반영 · 실데이터</span><span class="pg serif">16</span></div></div>''')

# 7 직렬별 전국
jrows = ''.join(f"<tr><td>{k}</td><td>{sl:,}</td><td class='cut'>{cm}</td><td class='rngcell'>{mn}~{mx}</td></tr>" for k,sl,mn,mx,cm in jr_nat)
PAGES.append(f'''<div class="page">
 <div class="rhead"><span class="r">PART 1 · 지방직 9급</span><span>1-3 직렬별</span></div>
 <div class="ptitle serif">직렬별 합격선 비교</div>
 <div class="psub">전국 · 2025년 · 선발 많은 순</div>
 <table class="dt"><thead><tr><th>직렬</th><th>선발</th><th>중앙</th><th>범위</th></tr></thead>
  <tbody>{jrows}</tbody></table>
 <div class="trend"><div class="tt"><span>직렬별 합격선 중앙값</span><b>단위: 점</b></div>
  <div class="bars">{''.join(f'<div class="bar"><div class="col" style="height:{cm}%"><span class="v">{cm}</span></div><span class="yr">{k[:2]}</span></div>' for k,sl,mn,mx,cm in jr_nat[:5])}</div></div>
 <div class="folio"><span class="src">상담 시 "직렬 전략" 근거 · 실데이터</span><span class="pg serif">40</span></div></div>''')

# 8 양성평등 (신규)
yrows = ''.join(f"<tr><td>{rg}</td><td>{jl}</td><td class='cut'>{c}</td><td style='color:var(--gold);font-weight:700'>{yv}</td><td>{c-yv}</td></tr>" for rg,yy,jl,c,yv in yp_samp)
PAGES.append(f'''<div class="page">
 <div class="rhead"><span class="r">PART 1 · 지방직 9급</span><span>1-4 양성평등</span></div>
 <div class="ptitle serif">양성평등 합격선</div>
 <div class="psub">양성평등채용목표제 적용 직렬 (전체 {yp_n}건 중 발췌)</div>
 <table class="dt"><thead><tr><th>지역·직렬</th><th></th><th>일반</th><th>양성</th><th>차</th></tr></thead>
  <tbody>{yrows}</tbody></table>
 <div class="note-box" style="margin-top:14px;"><div class="nt mono">차별화 콘텐츠</div>
  <p>한쪽 성별이 합격선에 못 미쳐도 <b>양성평등 합격선</b>으로 추가합격 가능. 타 교재에 거의 없는 정보로, 이 책만의 강점입니다.</p></div>
 <div class="folio"><span class="src">※ 항상 양성평등 ≤ 일반 합격선 · 실데이터</span><span class="pg serif">44</span></div></div>''')

# 9 PART3 도비라
PAGES.append('''<div class="page divider"><div class="dn mono">PART 3</div><h2 class="serif">지방<br>교육행정직</h2>
 <div class="dl"></div><p class="dd">17개 시·도교육청 9급 · 총점 기준.</p>
 <div class="dcontents">전국 종합 · · · 54<br>시도교육청별 · 56</div></div>''')

# 10 교행 전국 종합 (총점)
grows = ''.join(f"<tr><td>{y}</td><td>{gyo[y]['sel']:,}</td><td>{gyo[y]['app']:,}</td><td>{gyo[y]['comp']}</td><td class='cut'>{gyo[y]['cmed']}</td></tr>" for y in ('2023','2024','2025'))
PAGES.append(f'''<div class="page">
 <div class="rhead"><span class="r">PART 3 · 교육행정직</span><span>3-1 전국 종합</span></div>
 <div class="ptitle serif">교육행정 9급 · 전국</div>
 <div class="psub">전국 교육청 합산 · <b style="color:var(--red)">총점(500점) 기준</b></div>
 <table class="dt"><thead><tr><th>연도</th><th>선발</th><th>출원</th><th>경쟁</th><th>중앙</th></tr></thead>
  <tbody>{grows}</tbody></table>
 <div class="trend"><div class="tt"><span>경쟁률 추이</span><b>교행 高경쟁</b></div>
  <div class="bars">
   <div class="bar"><div class="col" style="height:{min(96,gyo['2023']['comp']*5):.0f}%"><span class="v">{gyo['2023']['comp']}</span></div><span class="yr">2023</span></div>
   <div class="bar"><div class="col" style="height:{min(96,gyo['2024']['comp']*5):.0f}%"><span class="v">{gyo['2024']['comp']}</span></div><span class="yr">2024</span></div>
   <div class="bar"><div class="col" style="height:{min(96,gyo['2025']['comp']*5):.0f}%"><span class="v">{gyo['2025']['comp']}</span></div><span class="yr">2025</span></div>
   <div class="bar future"><div class="col" style="height:55%"></div><span class="yr">2026</span></div></div></div>
 <div class="note-box" style="margin-top:12px;"><div class="nt mono">단위 주의</div><p>교행 합격선은 <b>총점(500점 만점)</b>이라 공무원 과목평균(100점)과 직접 비교 불가.</p></div>
 <div class="folio"><span class="src">출처: 시·도교육청 공고 · 실데이터</span><span class="pg serif">54</span></div></div>''')

# 11 시도 랭킹 (범위 — 광역시 vs 도 인사이트)
top5 = rank[:5]; bot3 = rank[-3:]
def rk_li(t, gold=False):
    med_,mn,mx,k,n = t
    rngtxt = f"{mn}~{mx}" if n>1 else "단일"
    col = "style='color:var(--gold)'" if gold else ""
    return f"<li><span class='pos mono' {col}>·</span><span class='nm'>{k}</span><span class='sc cut mono'>{med_}</span><span class='mt'>{rngtxt}</span></li>"
PAGES.append(f'''<div class="page">
 <div class="rhead"><span class="r">PART 4 · 비교·분석</span><span>4-2 랭킹</span></div>
 <div class="ptitle serif">시도 합격선 랭킹</div>
 <div class="psub">일반행정 9급 · 2025 · 중앙값 기준</div>
 <div class="rk-h mono">▲ 합격선 높은 시도 TOP 5</div>
 <ul class="rank">{''.join(rk_li(t) for t in top5)}</ul>
 <div class="rk-h mono" style="color:var(--gold)">▼ 진입 문턱 낮은 시도</div>
 <ul class="rank">{''.join(rk_li(t,True) for t in bot3)}</ul>
 <div class="note-box" style="margin-top:12px;"><div class="nt mono">핵심 인사이트</div>
  <p>광역시는 합격선 높고 <b>단일값</b>, 도(道)는 낮고 <b>시·군 편차 큼</b>(예: 강원 51~90). "도 지역+비인기 시군"이 전략 포인트.</p></div>
 <div class="folio"><span class="src">상담 "지역 전략" 근거 · 실데이터</span><span class="pg serif">70</span></div></div>''')

# 12 7급 (광역시 한정)
s7rows = ''.join(f"<tr><td>{jl}</td><td>{sl}</td><td>{ap:,}</td><td class='cut'>{c if c is not None else '-'}</td></tr>" for y,jl,sl,ap,c in s7r)
PAGES.append(f'''<div class="page">
 <div class="rhead"><span class="r">PART 2 · 지방직 7급</span><span>2-1 광역시 한정</span></div>
 <div class="ptitle serif">지방직 7급 <span style="font-size:.8rem;color:var(--gold)">서울 예시</span></div>
 <div class="psub">2023년 · 선발 많은 순</div>
 <table class="dt"><thead><tr><th>직렬</th><th>선발</th><th>출원</th><th>합격선</th></tr></thead>
  <tbody>{s7rows}</tbody></table>
 <div class="note-box" style="margin-top:14px;"><div class="nt mono">데이터 한계 — 솔직 고지</div>
  <p>7급 자료는 <b>{', '.join(metro7)} 광역시만</b> 확보됨. 도(道) 지역 7급은 미보유 → 본 PART는 "주요 광역시 한정"으로 수록하거나 2판/PDF에서 보강.</p></div>
 <div class="folio"><span class="src">※ 7급은 별도 시험(10/31) · 실데이터</span><span class="pg serif">46</span></div></div>''')

PAGE_HTML = '\n'.join(PAGES)

CSS = r'''
:root{--paper:#f7f3ec;--card:#fffdf9;--paper-2:#efe8db;--ink:#23262d;--ink-soft:#4a4742;--muted:#897f70;--line:#ddd3c2;--red:#b23a2e;--red-deep:#8f2c22;--gold:#bd8e3a;}
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:'IBM Plex Sans KR',sans-serif;color:var(--ink);background:#2a2d34;background-image:radial-gradient(circle at 50% 0%,#34373f,#232529 70%);min-height:100vh;-webkit-font-smoothing:antialiased;display:flex;flex-direction:column;align-items:center;}
.serif{font-family:'Nanum Myeongjo',serif;}.mono{font-family:'IBM Plex Mono',monospace;font-variant-numeric:tabular-nums;}
.bar{width:100%;max-width:760px;padding:18px 20px 6px;display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;}
.bar .t{color:#f3eee4;}.bar .t b{font-family:'Nanum Myeongjo',serif;font-weight:700;font-size:1rem;display:block;}
.bar .t span{font-family:'IBM Plex Mono',monospace;font-size:.7rem;color:#a59c8c;letter-spacing:.08em;}
.badge{background:rgba(123,180,110,.16);border:1px solid #7bb46e;color:#9ed18f;font-size:.68rem;padding:6px 11px;border-radius:20px;font-weight:600;white-space:nowrap;}
.viewer{width:100%;max-width:760px;padding:14px 20px 0;display:flex;justify-content:center;}
.stage-outer{position:relative;margin:0 auto;}
.stage{position:absolute;top:0;left:0;width:480px;height:681px;transform-origin:top left;}
.page{position:absolute;inset:0;background:var(--card);border-radius:3px;overflow:hidden;box-shadow:0 30px 60px rgba(0,0,0,.45);padding:36px 34px 26px;display:flex;flex-direction:column;opacity:0;transform:translateX(26px) scale(.985);transition:opacity .45s ease,transform .45s ease;pointer-events:none;}
.page.active{opacity:1;transform:none;pointer-events:auto;}
.page::before{content:"";position:absolute;left:0;top:0;bottom:0;width:6px;background:repeating-linear-gradient(var(--paper-2),var(--paper-2) 5px,transparent 5px,transparent 10px);opacity:.5;}
.rhead{display:flex;justify-content:space-between;align-items:baseline;font-family:'IBM Plex Mono',monospace;font-size:.6rem;letter-spacing:.1em;color:var(--muted);text-transform:uppercase;border-bottom:1px solid var(--line);padding-bottom:8px;}
.rhead .r{color:var(--red);font-weight:600;}
.ptitle{font-family:'Nanum Myeongjo',serif;font-weight:800;font-size:1.45rem;margin:14px 0 2px;letter-spacing:-.01em;}
.psub{font-size:.76rem;color:var(--muted);margin-bottom:14px;}
.folio{margin-top:auto;padding-top:10px;border-top:1px solid var(--line);display:flex;justify-content:space-between;align-items:center;}
.folio .src{font-size:.58rem;color:var(--muted);}.folio .pg{font-family:'Nanum Myeongjo',serif;font-weight:700;font-size:.95rem;}
.toc-kick{font-family:'IBM Plex Mono',monospace;font-size:.64rem;letter-spacing:.25em;color:var(--red);font-weight:600;}
.toc-h{font-family:'Nanum Myeongjo',serif;font-weight:800;font-size:1.9rem;margin:4px 0 18px;}
.toc-grp{margin-bottom:11px;}.toc-pn{font-family:'IBM Plex Mono',monospace;font-size:.66rem;color:var(--red);font-weight:600;}
.toc-pt{font-family:'Nanum Myeongjo',serif;font-weight:700;font-size:.98rem;margin:1px 0 4px;}
.toc-row{display:flex;align-items:baseline;font-size:.74rem;color:var(--ink-soft);padding:2px 0;}
.toc-row .lbl{white-space:nowrap;}.toc-row .dots{flex:1;border-bottom:1px dotted var(--line);margin:0 6px;transform:translateY(-3px);}
.toc-row .num{font-family:'IBM Plex Mono',monospace;color:var(--muted);font-size:.7rem;}
.term{padding:7px 0;border-bottom:1px solid var(--line);}.term:last-child{border:none;}
.term dt{font-family:'Nanum Myeongjo',serif;font-weight:700;font-size:.9rem;color:var(--ink);display:flex;align-items:baseline;gap:8px;}
.term dt .en{font-family:'IBM Plex Mono',monospace;font-size:.58rem;color:var(--gold);letter-spacing:.05em;}
.term dd{font-size:.74rem;color:var(--ink-soft);margin-top:1px;}.term dd .f{font-family:'IBM Plex Mono',monospace;color:var(--red);font-size:.7rem;}
.krit{margin-top:12px;display:grid;gap:7px;}
.kr{background:var(--paper);border-left:3px solid var(--red);padding:8px 11px;border-radius:0 5px 5px 0;font-size:.76rem;color:var(--ink-soft);}
.kr b{color:var(--red-deep);}
.big-stats{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:14px;}
.bstat{background:var(--paper);border:1px solid var(--line);border-radius:6px;padding:12px;}
.bstat .k{font-size:.64rem;color:var(--muted);letter-spacing:.03em;}
.bstat .v{font-family:'Nanum Myeongjo',serif;font-weight:800;font-size:1.4rem;color:var(--ink);line-height:1.1;margin:3px 0 1px;}
.bstat .v small{font-size:.8rem;}.bstat .d{font-family:'IBM Plex Mono',monospace;font-size:.66rem;font-weight:600;color:var(--muted);}
.down{color:var(--red);}.up{color:#6f9c5a;}
.note-box{background:#fbeee9;border-left:3px solid var(--red);padding:10px 12px;border-radius:0 5px 5px 0;}
.note-box .nt{font-size:.64rem;font-weight:700;color:var(--red-deep);letter-spacing:.06em;margin-bottom:3px;}
.note-box p{font-size:.73rem;color:var(--red-deep);line-height:1.5;}.note-box b{color:var(--red-deep);}
.page.divider{justify-content:center;align-items:center;text-align:center;background:linear-gradient(155deg,#2d3039,#1a1d22);padding:40px;}
.page.divider::before{display:none;}
.divider .dn{font-family:'IBM Plex Mono',monospace;color:var(--gold);letter-spacing:.35em;font-size:.82rem;}
.divider h2{font-family:'Nanum Myeongjo',serif;font-weight:800;color:var(--paper);font-size:2.4rem;margin:14px 0;line-height:1.1;}
.divider .dl{width:50px;height:3px;background:var(--red);margin:8px auto 16px;}
.divider .dd{color:#b8b1a3;font-size:.82rem;max-width:230px;line-height:1.6;}
.divider .dcontents{margin-top:22px;color:#8c8576;font-family:'IBM Plex Mono',monospace;font-size:.68rem;line-height:1.9;letter-spacing:.03em;}
.dt{width:100%;border-collapse:collapse;font-size:.74rem;margin-bottom:4px;}
.dt th{background:var(--ink);color:var(--paper);font-weight:600;font-size:.64rem;padding:6px 5px;text-align:right;}
.dt th:first-child{text-align:left;}
.dt td{padding:6px 5px;text-align:right;border-bottom:1px solid var(--line);font-family:'IBM Plex Mono',monospace;font-size:.72rem;}
.dt td:first-child{text-align:left;font-family:'IBM Plex Sans KR';font-weight:600;}
.dt tr:last-child td{border-bottom:none;}.dt .cut{color:var(--red);font-weight:700;}
.dt .rngcell{color:var(--ink-soft);font-size:.68rem;}.dt .tba{color:var(--muted);font-style:italic;font-family:'IBM Plex Sans KR';}
.dt tbody tr:nth-child(even) td{background:rgba(221,211,194,.18);}
.rbwrap{margin-top:14px;}.tt2{font-size:.68rem;color:var(--muted);margin-bottom:10px;}
.rb{margin-bottom:16px;}
.rb-track{position:relative;height:7px;background:var(--paper-2);border-radius:4px;margin:14px 0 2px;}
.rb-span{position:absolute;top:0;height:7px;background:linear-gradient(90deg,#e6b9a0,var(--red));border-radius:4px;}
.rb-med{position:absolute;top:-4px;width:2px;height:15px;background:var(--ink);}
.rb-med span{position:absolute;top:-15px;left:50%;transform:translateX(-50%);font-family:'IBM Plex Mono',monospace;font-size:.62rem;font-weight:700;color:var(--ink);}
.rb-lo,.rb-hi{position:absolute;top:9px;font-family:'IBM Plex Mono',monospace;font-size:.58rem;color:var(--muted);transform:translateX(-50%);}
.ryr{font-family:'IBM Plex Mono',monospace;font-size:.6rem;color:var(--muted);margin-top:-12px;margin-bottom:4px;}
.trend{margin-top:14px;}.trend .tt{font-size:.68rem;color:var(--muted);margin-bottom:8px;display:flex;justify-content:space-between;}
.trend .tt b{color:var(--ink);font-family:'IBM Plex Sans KR';}
.bars{display:flex;align-items:flex-end;gap:12px;height:88px;padding-top:16px;}
.bar{flex:1;display:flex;flex-direction:column;align-items:center;gap:5px;height:100%;justify-content:flex-end;}
.bar .col{width:60%;background:linear-gradient(var(--red),var(--red-deep));border-radius:3px 3px 0 0;position:relative;min-height:3px;}
.bar .col .v{position:absolute;top:-15px;left:-50%;right:-50%;text-align:center;font-family:'IBM Plex Mono',monospace;font-size:.6rem;color:var(--ink);font-weight:600;}
.bar .yr{font-family:'IBM Plex Mono',monospace;font-size:.62rem;color:var(--muted);}
.bar.future .col{background:repeating-linear-gradient(45deg,var(--line),var(--line) 4px,transparent 4px,transparent 8px);border:1px dashed var(--muted);}
.rk-h{font-family:'IBM Plex Mono',monospace;font-size:.62rem;color:var(--gold);font-weight:600;letter-spacing:.1em;margin:12px 0 5px;}
.rank{list-style:none;}.rank li{display:flex;align-items:center;gap:10px;padding:5px 0;border-bottom:1px solid var(--line);font-size:.78rem;}
.rank li:last-child{border-bottom:none;}.rank .pos{font-family:'IBM Plex Mono',monospace;font-weight:700;color:var(--red);width:14px;}
.rank .nm{flex:1;font-weight:500;}.rank .sc{font-family:'IBM Plex Mono',monospace;font-weight:700;}
.rank .mt{font-size:.64rem;color:var(--muted);width:54px;text-align:right;}
.controls{display:flex;align-items:center;justify-content:center;gap:8px;padding:18px 20px 30px;flex-wrap:wrap;}
.nav{background:var(--paper);color:var(--ink);border:none;width:42px;height:42px;border-radius:50%;font-size:1.1rem;cursor:pointer;box-shadow:0 4px 14px rgba(0,0,0,.3);transition:transform .15s,background .15s;display:flex;align-items:center;justify-content:center;}
.nav:hover{background:#fff;transform:translateY(-2px);}
.counter{color:#f3eee4;font-family:'IBM Plex Mono',monospace;font-size:.85rem;min-width:74px;text-align:center;letter-spacing:.08em;}
.dots{display:flex;gap:7px;width:100%;justify-content:center;margin-top:6px;}
.dot{width:8px;height:8px;border-radius:50%;background:#5a5d65;cursor:pointer;transition:background .2s,transform .2s;}
.dot.on{background:var(--gold);transform:scale(1.3);}
.hint{color:#80796c;font-size:.7rem;text-align:center;width:100%;margin-top:10px;font-family:'IBM Plex Mono',monospace;}
'''

JS = r'''
const BASE_W=480,BASE_H=681;const outer=document.getElementById('outer');const stage=document.getElementById('stage');
const pages=[...document.querySelectorAll('.page')];const counter=document.getElementById('counter');const dotsWrap=document.getElementById('dots');let i=0;
pages.forEach((_,k)=>{const d=document.createElement('div');d.className='dot'+(k===0?' on':'');d.addEventListener('click',()=>show(k));dotsWrap.appendChild(d);});
const dots=[...dotsWrap.children];
function fit(){const avail=outer.parentElement.clientWidth-40;let s=Math.min(1.25,avail/BASE_W);const maxH=window.innerHeight*0.76;s=Math.min(s,maxH/BASE_H);outer.style.width=(BASE_W*s)+'px';outer.style.height=(BASE_H*s)+'px';stage.style.transform='scale('+s+')';}
function show(n){i=(n+pages.length)%pages.length;pages.forEach((p,k)=>p.classList.toggle('active',k===i));dots.forEach((d,k)=>d.classList.toggle('on',k===i));counter.textContent=String(i+1).padStart(2,'0')+' / '+String(pages.length).padStart(2,'0');}
document.getElementById('prev').addEventListener('click',()=>show(i-1));document.getElementById('next').addEventListener('click',()=>show(i+1));
document.addEventListener('keydown',e=>{if(e.key==='ArrowLeft')show(i-1);if(e.key==='ArrowRight')show(i+1);});
window.addEventListener('resize',fit);fit();
'''

DOC = f'''<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>지방직·교행 합격선 포켓북 — 실데이터 개선 목업</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Nanum+Myeongjo:wght@400;700;800&family=IBM+Plex+Sans+KR:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body>
<div class="bar"><div class="t"><b>지방직·교행 합격선 포켓북 — 개선 목업</b><span>A5 · 실데이터 기반(2023~2025) · {len(PAGES)}p</span></div>
<div class="badge">✓ 실제 검증데이터 8,664행 집계</div></div>
<div class="viewer"><div class="stage-outer" id="outer"><div class="stage" id="stage">
{PAGE_HTML}
</div></div></div>
<div class="controls"><button class="nav" id="prev">‹</button><span class="counter mono" id="counter">01 / {len(PAGES):02d}</span>
<button class="nav" id="next">›</button><div class="dots" id="dots"></div>
<div class="hint mono">← → 키보드 · 좌우 버튼으로 페이지 넘기기</div></div>
<script>{JS}</script></body></html>'''

open(OUT, 'w', encoding='utf-8').write(DOC)
print('생성:', OUT, '| 페이지', len(PAGES))
print('전국 일반행정 2025 합격선:', nat['2025']['cmin'], '~', nat['2025']['cmax'], '중앙', nat['2025']['cmed'])
print('양성평등 행:', yp_n, '| 7급 광역시:', metro7)
