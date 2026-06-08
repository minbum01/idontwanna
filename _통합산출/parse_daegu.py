# -*- coding: utf-8 -*-
"""대구 공무원 합격선: hwp(PrvText 토큰) + pdf(/ 묶음) -> 통일 양식. 합격선=과목평균."""
import olefile, pdfplumber, re, os, glob, csv
ROOT=r"C:/Users/admin/Documents/이민범 개발/합격선/합격선 최종모음"
HEADERS=["지역","시험종류","연도","회차","시험구분","임용예정기관","직군","직렬","직류","직급","대상",
         "선발예정인원","접수인원","접수여성","경쟁률(접수/선발)","응시인원","응시여성","응시율","경쟁률(응시/선발)",
         "필기합격인원","필기합격여성","합격선","양성평등성별","양성평등합격선","최종합격인원","최종합격여성",
         "원본파일명","비고"]
JGRE=re.compile(r'^(\d+급|지도사|연구사|연구관)$')

def yr_rd(fn):
    y=re.search(r'(\d{4})',fn); r=re.search(r'제\s*(\d+)\s*회',fn)
    return (y.group(1) if y else ''),(r.group(1)+'회' if r else '')

def isnum(t):
    t=t.replace(',','').replace(' ','').strip()
    return t in ('-','–') or bool(re.match(r'^\d+(\.\d+)?$',t))

def num(t):
    t=t.replace(',','').replace(' ','').strip()
    return '' if t in ('','-','–') else t

def daenorm(s):
    s=s.replace(' ','')
    if '저소득' in s: return '저소득층'
    if '장애' in s: return '장애인'
    if '보훈' in s: return '보훈청추천'
    if '기술계' in s: return '기술계고졸'
    return s or '일반'

def pname(name):
    name=name.replace('/',' ')
    m=re.match(r'^(.+?)\s*\((.+?)\)',name)
    if m:
        jr=m.group(1).strip(); ju=m.group(2).strip()
    else:
        jr=name.strip(); ju=jr
    if jr.endswith('직') and len(jr)>1: jr=jr[:-1]
    jr=re.sub(r'\s+','',jr); ju=re.sub(r'\s+','',ju)
    return jr,ju

def prvtext(p):
    o=olefile.OleFileIO(p); d=o.openstream('PrvText').read().decode('utf-16-le','ignore'); o.close(); return d

def parse_hwp(path,yr,rd):
    toks=re.findall(r'<(.*?)>', prvtext(path), flags=re.S)
    out=[]; cur_g=''; cur_jr=cur_ju=''
    # 헤더('구분') 이후
    start=0
    for k,t in enumerate(toks):
        if t.replace(' ','').startswith('구분'): start=k+1; break
    i=start; n=len(toks)
    def gub(s): return s in ('공채','경채','공개경쟁','경력경쟁')
    has_gubun=any(gub(t.replace(' ','')) for t in toks)
    file_flag=''
    if not has_gubun:
        cur_g='경력경쟁' if rd=='3회' else '공개경쟁'
        file_flag='시험구분 원본미표기(회차로 추정)'
    while i<n:
        nm=toks[i].replace(' ','')
        if gub(nm):
            cur_g='공개경쟁' if nm.startswith('공') else '경력경쟁'; i+=1; continue
        if nm.startswith('소계'):
            i+=1
            c=0
            while i<n and isnum(toks[i]) and c<5: i+=1; c+=1
            continue
        labels=[]
        while i<n and not isnum(toks[i]) and not gub(toks[i].replace(' ','')) and not toks[i].replace(' ','').startswith('소계'):
            labels.append(toks[i]); i+=1
        nums=[]
        while i<n and isnum(toks[i]) and len(nums)<5: nums.append(toks[i]); i+=1
        if len(nums)<5: continue
        jikgup=''; daesang='일반'
        for L in labels:
            if '(' in L:
                cur_jr,cur_ju=pname(L)
            elif JGRE.match(L.replace(' ','')):
                jikgup=L.replace(' ','')
            else:
                daesang=daenorm(L)
        sel,chul,eung,hap,cut=[num(x) for x in nums]
        out.append(["대구","공무원",yr,rd,cur_g,"","",cur_jr,cur_ju,jikgup,daesang,
                    sel,chul,"","",eung,"","","",hap,"",cut,"","","","",os.path.basename(path),file_flag])
    return out

def parse_pdf(path,yr,rd):
    with pdfplumber.open(path) as pdf:
        tabs=[p.extract_table() for p in pdf.pages]
    out=[]; cur_g=''
    for t in tabs:
        if not t: continue
        ncol=max(len(r) for r in t)
        has_g = ncol>=9
        file_flag=''
        if not has_g:
            cur_g='경력경쟁' if rd=='3회' else '공개경쟁'; file_flag='시험구분 원본미표기(회차로 추정)'
        for r in t:
            c=[(x or '') for x in (list(r)+['']*ncol)[:ncol]]
            if has_g:
                gg,cjik,cdae,cjg,c4,c5,c6,c7,c8 = c[0],c[1],c[2],c[3],c[4],c[5],c[6],c[7],c[8]
            else:
                gg=''; cjik,cdae,cjg,c4,c5,c6,c7,c8 = c[0],c[1],c[2],c[3],c[4],c[5],c[6],c[7]
            if '직렬' in cjik.replace('\n','') or cjik.replace(' ','') in ('총계','계','구분',''): continue
            g=gg.replace('\n','').replace('/','').replace(' ','')
            if '공채' in g or '공개' in g: cur_g='공개경쟁'
            elif '경채' in g or '경력' in g: cur_g='경력경쟁'
            jr,ju=pname(cjik)
            jikgup=cjg.replace('\n','').replace('/','').strip()
            c2=cdae
            ds=[daenorm(x) for x in c2.split('/')] if c2.strip() else ['일반']
            N=len(ds)
            def sp(x):
                v=[y for y in x.replace('\n','/').split('/') if y.strip()!='']
                return v
            sel=sp(c4); chul=sp(c5); eung=sp(c6); hap=sp(c7); cut=sp(c8)
            def pk(L,k): return L[k] if k<len(L) else (L[-1] if len(L)==1 else '')
            for k in range(N):
                out.append(["대구","공무원",yr,rd,cur_g,"","",jr,ju,jikgup,ds[k],
                            num(pk(sel,k)),num(pk(chul,k)),"","",num(pk(eung,k)),"","","",num(pk(hap,k)),"",
                            num(pk(cut,k)),"","","","",os.path.basename(path),file_flag])
    return out

if __name__=='__main__':
    out=[]
    folder=os.path.join(ROOT,'03 대구 공무원')
    for f in sorted(glob.glob(os.path.join(folder,'*'))):
        fn=os.path.basename(f); ext=os.path.splitext(fn)[1].lower()
        if '합격선' not in fn: continue   # 출원자현황 제외
        yr,rd=yr_rd(fn)
        try:
            r=parse_hwp(f,yr,rd) if ext=='.hwp' else (parse_pdf(f,yr,rd) if ext=='.pdf' else [])
            print(f"{fn[:50]:50} -> {len(r)}")
            out+=r
        except Exception as e:
            print(fn,'ERR',e)
    OUT=os.path.join(os.path.dirname(__file__),'대구_공무원.csv')
    with open(OUT,'w',encoding='utf-8-sig',newline='') as fp:
        w=csv.writer(fp); w.writerow(HEADERS); w.writerows(out)
    print('TOTAL',len(out),'->',OUT)
    print('--- sample ---')
    for r in out[:6]+out[-4:]: print(r[2:12]+[r[12],r[15],r[19],r[21]])
