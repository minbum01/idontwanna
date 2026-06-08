# -*- coding: utf-8 -*-
"""시·군 임용기관별 통계/합격선(직렬직급직류+임용기관+합격선평균) 범용 파서: 강원·충북·충남·전북 공무원.
pdf+xlsx 헤더 인식. 합격선=과목평균. parse_jik으로 '간호8급(간호)'/'행정9급(일반행정)[_대상]' 분해."""
import pdfplumber, openpyxl, re, os, glob, csv
ROOT=r"C:/Users/admin/Documents/이민범 개발/합격선/합격선 최종모음"
HEADERS=["지역","시험종류","연도","회차","시험구분","임용예정기관","직군","직렬","직류","직급","대상",
         "선발예정인원","접수인원","접수여성","경쟁률(접수/선발)","응시인원","응시여성","응시율","경쟁률(응시/선발)",
         "필기합격인원","필기합격여성","합격선","양성평등성별","양성평등합격선","최종합격인원","최종합격여성",
         "원본파일명","비고"]
TARGETS=[('09 강원 공무원','강원'),('10 충북 공무원','충북'),('11 충남 공무원','충남'),('12 전북 공무원','전북'),
         ('13 전남 공무원','전남'),('14 경북 공무원','경북'),('15 경남 공무원','경남'),('16 제주 공무원','제주'),('17 세종 공무원','세종')]

def num(t):
    t=re.sub(r'[,\s명점]','',str(t or ''))
    return '' if t in ('','-','–','비공개') else t
def daenorm(s):
    s=re.sub(r'\s+','',str(s))
    if '저소득' in s: return '저소득층'
    if '장애' in s: return '장애인'
    if '보훈' in s: return '보훈청추천'
    if '지방의회' in s: return '지방의회'
    return s or '일반'
def parse_jik(s):
    s=str(s).replace('\n','').strip()
    m=re.match(r'^(\D+?)(\d+급|연구사|지도사)\s*\((.+?)\)\s*(.*)$', s)
    if m:
        jr,jg,inner,tail=m.group(1),m.group(2),m.group(3),m.group(4)
        if '_' in inner: ju,dae=inner.rsplit('_',1)
        else: ju,dae=inner,(tail or '일반')
    else:
        m2=re.match(r'^(.+?)\s*\((.+?)\)\s*(.*)$', s)
        if m2: jr,ju,dae=m2.group(1),m2.group(2),(m2.group(3) or '일반'); jg=''
        else:
            m3=re.match(r'^(.+?)\s*(\d+급|연구사|지도사)$', s)
            if m3: jr=ju=m3.group(1); jg=m3.group(2)
            else: jr=ju=s; jg=''
        dae=dae if 'dae' in dir() else '일반'
    jr=re.sub(r'\s+','',jr); ju=re.sub(r'\s+','',ju)
    if jr.endswith('직') and len(jr)>1: jr=jr[:-1]
    return jr,ju,jg,daenorm(dae)
def yr_rd(fn):
    y=re.search(r'(\d{4})',fn); r=re.search(r'제\s*(\d+)\s*회',fn)
    return (y.group(1) if y else ''),(r.group(1)+'회' if r else '')
def hidx(H,kw,*ex):
    for i,c in enumerate(H):
        cc=str(c or '').replace('\n','').replace(' ','')
        if kw in cc and not any(e in cc for e in ex): return i
    return -1

def rows_from(path):
    if path.lower().endswith('.xlsx'):
        wb=openpyxl.load_workbook(path,data_only=True); ws=wb[wb.sheetnames[0]]
        return [[('' if c is None else c) for c in r] for r in ws.iter_rows(values_only=True)]
    out=[]
    with pdfplumber.open(path) as pdf:
        for p in pdf.pages:
            t=p.extract_table()
            if t: out+=t
    return out

def get_blob(path):
    try:
        if path.lower().endswith(('.xlsx','.xls')): return ''
        with pdfplumber.open(path) as pdf:
            return (pdf.pages[0].extract_text() or '')[:200]
    except: return ''

def parse(path, region):
    fn=os.path.basename(path); yr,rd=yr_rd(fn)
    rows=rows_from(path)
    if not yr or not rd:
        blob=fn+' '+(' '.join(str(c) for r in rows[:6] for c in r if c))+' '+get_blob(path)
        if not yr:
            m=re.search(r'(20\d{2})\s*년', blob); yr=m.group(1) if m else ''
        if not rd:
            m=re.search(r'제\s*(\d+)\s*회', blob); rd=(m.group(1)+'회') if m else '1회'
    def has(c,kw): return kw in str(c).replace(' ','')
    hi=next((i for i,r in enumerate(rows) if any(has(c,'직렬') or has(c,'직급') for c in r if c) and any(has(c,'임용') or has(c,'기관') for c in r if c)),None)
    if hi is None: hi=next((i for i,r in enumerate(rows) if any(has(c,'직렬') for c in r if c)),None)
    if hi is None: return []
    H=rows[hi]
    i_jik=hidx(H,'직렬'); i_gig=hidx(H,'임용') if hidx(H,'임용')>=0 else hidx(H,'기관')
    i_sel=hidx(H,'선발'); i_chul=hidx(H,'출원') if hidx(H,'출원')>=0 else hidx(H,'접수')
    i_eung=hidx(H,'응시','율'); i_hap=hidx(H,'필기합격','선')
    if i_hap<0: i_hap=hidx(H,'합격인원')
    if i_hap<0: i_hap=hidx(H,'합격','선','양성')
    i_cut=hidx(H,'합격선','양성','초과'); i_yang=hidx(H,'양성')
    if i_cut<0: i_cut=hidx(H,'합격선')
    if i_jik<0 or i_cut<0: return []
    def g(c,i): return c[i] if (0<=i<len(c)) else ''
    out=[]; cur=None
    for r in rows[hi+1:]:
        c=[('' if x is None else x) for x in r]
        jik=str(g(c,i_jik)).strip()
        if jik and not re.match(r'^\s*(소계|총계|계|합계)',jik) and '직렬' not in jik:
            cur=parse_jik(jik)
        gig=str(g(c,i_gig)).replace('\n',' ').strip() if i_gig>=0 else ''
        if not cur: continue
        if re.match(r'^\s*(소계|총계|합계|계)\s*$',gig): continue
        cut=num(g(c,i_cut))
        hap=num(g(c,i_hap)) if i_hap>=0 else ''
        if cut=='' and hap=='' : continue
        if i_gig>=0 and gig=='' and i_sel>=0 and num(g(c,i_sel))=='' and cut=='': continue
        out.append([region,"공무원",yr,rd or "1회","공개경쟁",gig,"",cur[0],cur[1],cur[2],cur[3],
                    num(g(c,i_sel)) if i_sel>=0 else "", num(g(c,i_chul)) if i_chul>=0 else "","","",
                    num(g(c,i_eung)) if i_eung>=0 else "","","","", hap,"", cut,"",
                    num(g(c,i_yang)) if i_yang>=0 else "","","",fn,""])
    return out

if __name__=='__main__':
    out=[]
    for folder,region in TARGETS:
        for f in sorted(glob.glob(os.path.join(ROOT,folder,'*.pdf'))+glob.glob(os.path.join(ROOT,folder,'*.xlsx'))):
            fn=os.path.basename(f)
            if ('합격선' not in fn and '합격자' not in fn) or '접수' in fn or '현황' in fn or '출원' in fn or '응시' in fn: continue
            try:
                r=parse(f,region); print(f"{region} {fn[:30]:30} -> {len(r)}"); out+=r
            except Exception as e: print(fn[:30],'ERR',e)
    OUT=os.path.join(os.path.dirname(__file__),'신규4_공무원.csv')
    with open(OUT,'w',encoding='utf-8-sig',newline='') as fp:
        w=csv.writer(fp); w.writerow(HEADERS); w.writerows(out)
    from collections import Counter
    print('TOTAL',len(out),dict(Counter(r[0] for r in out)))
    for r in out[:3]+out[-3:]: print(r[0],r[2],r[5],r[7],r[8],r[9],r[10],'선발',r[11],'합격',r[19],'합격선',r[21])
