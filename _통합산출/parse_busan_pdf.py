# -*- coding: utf-8 -*-
"""부산 공무원 PDF(합격선) -> 통일 양식. 한 셀에 여러 직류가 줄바꿈으로 묶인 양식."""
import pdfplumber, re, os, glob, csv

ROOT = r"C:/Users/admin/Documents/이민범 개발/합격선/합격선 최종모음"
HEADERS = ["지역","시험종류","연도","회차","시험구분","임용예정기관","직군","직렬","직류","직급","대상",
           "선발예정인원","접수인원","접수여성","경쟁률(접수/선발)","응시인원","응시여성","응시율","경쟁률(응시/선발)",
           "필기합격인원","필기합격여성","합격선","양성평등성별","양성평등합격선","최종합격인원","최종합격여성",
           "원본파일명","비고"]

def clean(s):
    return re.sub(r'\s+','', s or '')

def num(t):
    t=(t or '').replace(',','').strip()
    if t in ('','-','–','-'): return ''
    return t

def parse_name(tok):
    name=re.sub(r'-+',' ',tok).strip()
    m=re.match(r'^(.+?)\((.+?)\)\s*(.*)$', name)
    if not m: return (name,name,'일반')
    jikryeol=m.group(1).strip(); jikryu=m.group(2).strip(); rest=m.group(3).strip()
    if jikryeol.endswith('직') and len(jikryeol)>1: jikryeol=jikryeol[:-1]
    daesang='일반'
    if '장애' in rest: daesang='장애인'
    elif '저소득' in rest: daesang='저소득층'
    elif rest: daesang=rest.lstrip('_')
    return jikryeol,jikryu,daesang

def parse_pdf(path, region, kind, yr, rd):
    rows=[]
    with pdfplumber.open(path) as pdf:
        tables=[p.extract_table() for p in pdf.pages]
    cur_gubun=cur_jikgun=''
    for t in tables:
        if not t: continue
        for row in t:
            c=[ (x or '') for x in (list(row)+['']*10)[:10] ]
            c0,c1,c2,c3,c4,c5,c6,c7,c8 = c[0],c[1],c[2],c[3],c[4],c[5],c[6],c[7],c[8]
            if '직렬' in clean(c2) or clean(c0)=='구분': continue          # 헤더
            if clean(c0).startswith('계') or clean(c2)=='' and clean(c4) and not c2:
                if clean(c0).startswith('계'): continue
            if not c2.strip(): continue
            g0=clean(c0)
            if g0:
                if '공개' in g0: cur_gubun='공개경쟁'
                elif '경력' in g0: cur_gubun='경력경쟁'
                else: cur_gubun=g0
            if clean(c1): cur_jikgun=clean(c1)
            jr=[x for x in c2.split('\n') if x.strip()]
            N=len(jr)
            if N==0: continue
            def col(x):
                v=[y for y in (x or '').split('\n') if y.strip()!='']
                return v
            jg=col(c3); sel=col(c4); chul=col(c5); eung=col(c6); hap=col(c7); cut=col(c8)
            flag=''
            if not jg: jg=['']*N
            elif len(jg)==1: jg=jg*N                      # 단일 직급 → 전체 적용(명확)
            elif len(jg)<N:                                # 서로 다른 직급이 부족 → 애매
                jg=jg+[jg[-1]]*(N-len(jg)); flag='직급확인'
            def pick(lst,k): return lst[k] if k<len(lst) else ''
            for k in range(N):
                jikryeol,jikryu,daesang=parse_name(jr[k])
                rows.append([region,kind,yr,rd,cur_gubun,'',cur_jikgun,jikryeol,jikryu,pick(jg,k),daesang,
                             num(pick(sel,k)),num(pick(chul,k)),'','',num(pick(eung,k)),'','','',num(pick(hap,k)),'',
                             num(pick(cut,k)),'','','','',os.path.basename(path),flag])
    return rows

def meta(folder, fn):
    name=re.sub(r'^\d+\s*','',folder).strip(); parts=name.split()
    region=parts[0]; kind=' '.join(parts[1:]) if len(parts)>1 else ''
    y=re.search(r'(\d{4})',fn); r=re.search(r'제\s*(\d+)\s*회',fn)
    return region,kind,(y.group(1) if y else ''),(r.group(1)+'회' if r else '')

if __name__=='__main__':
    out=[]
    targets=[f for f in glob.glob(os.path.join(ROOT,'*','*.pdf'))
             if '부산' in os.path.basename(os.path.dirname(f))
             and '공무원' in os.path.basename(os.path.dirname(f)) and '합격선' in os.path.basename(f)]
    for f in sorted(targets):
        folder=os.path.basename(os.path.dirname(f)); fn=os.path.basename(f)
        region,kind,yr,rd=meta(folder,fn)
        r=parse_pdf(f,region,kind,yr,rd)
        print(f"{fn} -> {len(r)} rows")
        out+=r
    OUT=os.path.join(os.path.dirname(__file__),'부산_공무원_pdf.csv')
    with open(OUT,'w',encoding='utf-8-sig',newline='') as fp:
        w=csv.writer(fp); w.writerow(HEADERS); w.writerows(out)
    print('TOTAL',len(out),'->',OUT)
    for r in out: print(r[2:12]+[r[16],r[19],r[21],r[27]])
