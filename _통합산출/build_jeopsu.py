# -*- coding: utf-8 -*-
"""2026 원서접수현황 3종(서울교행 판독, 부산공무원·부산교행 pdfplumber) -> 별도 시트용 CSV.
계산: 경쟁률(접수/선발). 응시 데이터 없어 응시율 등은 공란."""
import pdfplumber, glob, os, re, csv
base=r'C:/Users/admin/Documents/이민범 개발/합격선/합격선 최종모음'
HEADERS = ["지역","시험종류","연도","회차","시험구분","임용예정기관","직군","직렬","직류","직급","대상",
           "선발예정인원","접수인원","접수여성","경쟁률(접수/선발)","응시인원","응시여성","응시율","경쟁률(응시/선발)",
           "필기합격인원","필기합격여성","합격선","양성평등성별","양성평등합격선","최종합격인원","최종합격여성",
           "원본파일명","비고"]

def n(t):
    t=re.sub(r'[명,\s]','',str(t or ''));
    return t if t not in ('','-','–') else ''

def ratio(sel,sin):
    try:
        s=float(sel); a=float(sin)
        if s>0: return "%.1f:1"%(a/s)
    except: pass
    return ''

def split_name(tok):
    name=re.sub(r'-+',' ',tok).strip()
    m=re.match(r'^(.+?)\((.+?)\)\s*(.*)$', name)
    if m:
        jr=m.group(1).strip(); ju=m.group(2).strip(); rest=m.group(3).strip()
    else:
        jr=name; ju=name; rest=''
    if jr.endswith('직') and len(jr)>1: jr=jr[:-1]
    daesang='일반'
    if '장애' in rest: daesang='장애인'
    elif '저소득' in rest: daesang='저소득층'
    elif rest: daesang=rest.lstrip('_')
    return jr,ju,daesang

rows=[]
def emit(지역,종류,연도,회차,fn,gubun,jikgun,jr,ju,jg,ds,sel,sin,yeo='',비고=''):
    rows.append([지역,종류,연도,회차,gubun,"",jikgun,jr,ju,jg,ds,
                 sel,sin,yeo,ratio(sel,sin),"","","","","","","","","","","",fn,비고])

# ===== 서울 교행 2026 (이미지 판독) =====
FS="2026년도 제1회 서울특별시교육청 지방공무원 9급 공개(경력)경쟁임용시험 원서접수결과(게시용).pdf"
def es(g,jr,ju,ds,sel,sin): emit("서울","교행","2026","1회",FS,g,"",jr,ju,"9급",ds,str(sel),str(sin))
es("공개경쟁","교육행정","교육행정","일반",316,2909)
es("공개경쟁","교육행정","교육행정","장애인",30,111)
es("공개경쟁","교육행정","교육행정","저소득층",5,65)
es("공개경쟁","사서","사서","일반",42,618)
es("공개경쟁","사서","사서","장애인",6,14)
es("공개경쟁","사서","사서","저소득층",2,7)
es("공개경쟁","공업","일반전기","일반",4,21)
es("경력경쟁","시설관리","시설관리","일반",47,386)
es("경력경쟁","시설관리","시설관리","저소득층",2,7)
es("경력경쟁","시설관리","시설관리","국가유공자",15,13)

# ===== 부산 공무원 2026 (pdfplumber) =====
FB=glob.glob(os.path.join(base,'02 부산 공무원','*응시원서 접수*.pdf'))[0]
with pdfplumber.open(FB) as pdf:
    t=pdf.pages[0].extract_table()
cur_g=cur_jg=cur_jik=''
for r in t:
    c=[(x or '') for x in (list(r)+['']*9)[:9]]
    c0,c1,c2,c3,c4,c5,c6,c7,c8=c
    if '직렬' in c0.replace('\n','') or '개 직렬' in c0 or c0.startswith('19개'): continue
    if not c2.strip(): continue
    g=c0.replace('\n','').replace(' ','')
    if '공개' in g: cur_g='공개경쟁'
    elif '경력' in g: cur_g='경력경쟁'
    jk=c1.replace('\n','').replace(' ','')
    if jk: cur_jik=jk
    if c3.strip(): cur_jg=c3.strip()
    jr,ju,ds=split_name(c2)
    note=("전년경쟁률 %s"%c7.replace('\n','') if c7.strip() else "")
    if c8.strip(): note=(note+" "+c8.replace('\n','')).strip()
    emit("부산","공무원","2026","1회",os.path.basename(FB),cur_g,cur_jik,jr,ju,cur_jg,ds,n(c4),n(c5),비고=note)

# ===== 부산 교행 2026 (pdfplumber, 남/여 분해) =====
FG=[f for f in glob.glob(os.path.join(base,'02 부산 교행','*접수현황*.pdf')) if '2026' in os.path.basename(f)][0]
with pdfplumber.open(FG) as pdf:
    t=pdf.pages[0].extract_table()
cur_g=cur_mo=''
JGRE=re.compile(r'(\d+급|연구사|지도사)\s*$')
for r in t:
    c=[(x or '') for x in (list(r)+['']*10)[:10]]
    c0,c1,c2,c3,c4=c[0],c[1],c[2],c[3],c[4]
    c5,c7,c9=c[5],c[7],c[9]
    mo=c1.replace('\n',' ').strip()
    if c0.replace(' ','') in ('구분','합계','합 계') or '원서접수' in (c4 or ''): continue
    if not c3.strip(): continue
    g=c0.replace(' ','')
    if '공개' in g: cur_g='공개경쟁'
    elif '경력' in g: cur_g='경력경쟁'
    if mo: cur_mo=mo
    name=cur_mo
    mjg=JGRE.search(name); jg=mjg.group(1) if mjg else '9급'
    base_name=JGRE.sub('', name).strip().rstrip('/').strip()
    jr,ju,_=split_name(base_name)
    ds=c2.strip() or '일반'
    if '장애' in ds: ds='장애인'
    elif '저소득' in ds: ds='저소득층'
    yeo=''
    m=re.match(r'\s*([\d,]+)', c7 or '')
    if m: yeo=m.group(1).replace(',','')
    emit("부산","교행","2026","1회",os.path.basename(FG),cur_g,"",jr,ju,jg,ds,n(c3),n(c4),yeo=yeo)

# ===== 대구 교행 2026 제2회 (접수결과, 단순표) =====
FD="2026년도+제2회+대구광역시교육청+지방공무원+공개·경력경쟁임용시험+원서접수+결과.pdf"
def ed(g,jr,ju,ds,sel,sin): emit("대구","교행","2026","2회",FD,g,"",jr,ju,"9급",ds,str(sel),str(sin))
ed("공개경쟁","교육행정","교육행정","일반",48,1036)
ed("공개경쟁","교육행정","교육행정","장애인",3,28)
ed("공개경쟁","교육행정","교육행정","저소득층",2,18)
ed("공개경쟁","사서","사서","일반",8,110)
ed("경력경쟁","운전","운전","일반",1,1)

# ===== 대구 공무원 2026 제2회 출원자현황 =====
FDG=glob.glob(os.path.join(base,'03 대구 공무원','*출원자 현황*.pdf'))
if FDG:
    with pdfplumber.open(FDG[0]) as pdf:
        t=pdf.pages[0].extract_table()
    cur=('','','')
    for r in t:
        c=[(x or '') for x in (list(r)+['']*6)[:6]]
        c0,c1,c2,c3,c4=c[0],c[1],c[2],c[3],c[4]
        if '직렬' in c1.replace('\n','') or c0.replace(' ','')=='연번': continue
        if not c3.strip() and not c4.strip(): continue
        if c1.strip():
            m=re.match(r'^(.+?)\((.+?)\)(?:_?\s*(\S*급))?',c1.replace('\n',''))
            if m:
                jr=m.group(1).strip(); ju=m.group(2).strip(); jg=(m.group(3) or '9급').strip()
                if jr.endswith('직') and len(jr)>1: jr=jr[:-1]
                cur=(jr,ju,jg)
        if not c3.strip(): continue   # 계 행
        ds=c2.replace(' ','') or '일반'
        if '장애' in ds: ds='장애인'
        elif '저소득' in ds: ds='저소득층'
        emit("대구","공무원","2026","2회",os.path.basename(FDG[0]),"공개경쟁","",cur[0],cur[1],cur[2],ds,
             n(c3),n(c4),비고="시험구분 미표기(제2회 공채로 추정)")

# ===== 서울 공무원 2026 제1회 현황(원서접수 단계, 합격선 없음) =====
FS26=glob.glob(os.path.join(base,'01 서울 공무원','2026*현황*.pdf'))
if FS26:
    with pdfplumber.open(FS26[0]) as pdf:
        tabs=[p.extract_table() for p in pdf.pages]
    cur_g='공개경쟁'; cur_jik=''
    for t in tabs:
        if not t: continue
        for r in t:
            c=[(x or '') for x in (list(r)+['']*7)[:7]]
            t0=c[0].replace('\n','').replace(' ','')
            if '경력경쟁' in t0: cur_g='경력경쟁'
            elif '공개경쟁' in t0: cur_g='공개경쟁'
            jik=c[1].replace('\n','').strip()
            jikgup=c[3].replace('\n','').replace(' ','').strip()
            if not re.match(r'\d+급$',jikgup): continue   # leaf만(직급 있음)
            if jik and not jik.endswith('직군') and '소계' not in jik: cur_jik=jik
            juraw=c[2].replace('\n','').strip()
            m=re.match(r'^(.+?)\((.+?)\)$',juraw)
            if m: ju, dae = m.group(1).strip(), m.group(2).strip()
            else: ju, dae = juraw, '일반'
            if '장애' in dae: dae='장애인'
            elif '저소득' in dae: dae='저소득층'
            emit("서울","공무원","2026","1회",os.path.basename(FS26[0]),cur_g,"",cur_jik,ju,jikgup,dae,
                 n(c[4]),n(c[5]),비고="원서접수 단계(합격선 미발표)")

# ===== 광주 공무원 2026 제1회 최종접수현황 =====
FGW=glob.glob(os.path.join(base,'05 광주 공무원','2026*최종접수현황*.pdf'))
if FGW:
    with pdfplumber.open(FGW[0]) as pdf:
        tabs=[p.extract_table() for p in pdf.pages]
    cur=('','','')
    for t in tabs:
        if not t: continue
        for r in t:
            c=[(x or '') for x in (list(r)+['']*9)[:9]]
            jik=c[2].replace('\n','').strip(); dae=c[3].replace('\n','').strip()
            jg=c[4].replace('\n','').replace(' ','').strip()
            if '직렬' in jik or c[0].replace(' ','') in ('계','총계','시험명'): continue
            if jik and '소계' not in jik and '계' not in jik.replace(' ',''):
                j2,u2,_=split_name(jik); cur=(j2,u2,jg or '9급')
            if not dae or '구분' in dae or '소계' in dae: continue
            ds=dae.replace(' ','')
            if '장애' in ds: ds='장애인'
            elif '저소득' in ds: ds='저소득층'
            elif not ds: ds='일반'
            emit("광주","공무원","2026","1회",os.path.basename(FGW[0]),"공개경쟁","",cur[0],cur[1],jg or cur[2],ds,
                 n(c[5]),n(c[6]),비고="시험구분 미표기(제1회 공개로 가정)")

OUT=os.path.join(os.path.dirname(__file__),"접수현황_data.csv")
with open(OUT,"w",encoding="utf-8-sig",newline="") as fp:
    w=csv.writer(fp); w.writerow(HEADERS); w.writerows(rows)
from collections import Counter
print("접수현황 rows:",len(rows),"->",OUT)
print(Counter((r[0],r[1]) for r in rows))
for r in rows: print(r[0],r[4],r[7],r[8],r[9],r[10],'선발',r[11],'접수',r[12],'여',r[13],'경쟁',r[14])
