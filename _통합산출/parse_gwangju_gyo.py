# -*- coding: utf-8 -*-
"""광주 교행 합격선: 2023·2025 pdf(표) + 2024 hwpx(셀스트림) -> 통일 양식. 합격선=총점."""
import pdfplumber, re, os, glob, csv, zipfile, importlib.util
ROOT=r"C:/Users/admin/Documents/이민범 개발/합격선/합격선 최종모음/05 광주 교행"
HEADERS=["지역","시험종류","연도","회차","시험구분","임용예정기관","직군","직렬","직류","직급","대상",
         "선발예정인원","접수인원","접수여성","경쟁률(접수/선발)","응시인원","응시여성","응시율","경쟁률(응시/선발)",
         "필기합격인원","필기합격여성","합격선","양성평등성별","양성평등합격선","최종합격인원","최종합격여성",
         "원본파일명","비고"]
_h=importlib.util.spec_from_file_location('h',os.path.join(os.path.dirname(__file__),'hwp5_text.py'))
H5=importlib.util.module_from_spec(_h); _h.loader.exec_module(H5)
JG=re.compile(r'^(\d+급|연구사|지도사)$')
def num(t):
    t=str(t).replace(',','').replace(' ','').strip()
    return '' if t in ('','-','–') else t
def daenorm(s):
    s=re.sub(r'\s+','',s)
    if '저소득' in s: return '저소득층'
    if '장애' in s: return '장애인'
    if '보훈' in s: return '보훈청추천'
    return s or '일반'
def gub(s):
    s=s.replace(' ','')
    if '공개' in s or '공채' in s: return '공개경쟁'
    if '경력' in s or '경채' in s: return '경력경쟁'
    return ''
def split_jik(s):
    s=s.replace('\n','').strip()
    m=re.match(r'^(.+?)\s*\((.+?)\)\s*$',s)
    if m: jr,ju=re.sub(r'\s+','',m.group(1)),re.sub(r'\s+','',m.group(2))
    else: jr=ju=re.sub(r'\s+','',s)
    if jr.endswith('직') and len(jr)>1: jr=jr[:-1]
    return jr,ju
def yr_of(fn):
    m=re.search(r'(\d{4})',fn); return m.group(1) if m else ''

def parse_pdf(path):
    fn=os.path.basename(path); yr=yr_of(fn); rd=(re.search(r"제s*(d+)s*회",fn).group(1)+"회") if re.search(r"제s*(d+)s*회",fn) else "1회"
    with pdfplumber.open(path) as pdf:
        tab=None
        for p in pdf.pages:
            t=p.extract_text() or ''
            if '합격선' in t and ('교육행정' in t or '직 렬' in t): tab=p.extract_table(); break
    if not tab: return []
    H=tab[0]
    def idx(kw,*ex):
        for i,c in enumerate(H):
            cc=(c or '').replace('\n','').replace(' ','')
            if kw in cc and not any(e in cc for e in ex): return i
        return -1
    i_m=idx('시험방법'); i_jik=idx('직렬'); i_dae=idx('구분'); i_jg=idx('직급')
    i_sel=idx('선발'); i_hap=idx('필기'); i_cut=idx('합격선')
    out=[]; cur_g=cur_jr=cur_ju=''
    for r in tab[1:]:
        c=[(x or '') for x in r]
        def g(i): return c[i] if 0<=i<len(c) else ''
        if gub(g(i_m)): cur_g=gub(g(i_m))
        jik=g(i_jik).strip()
        if jik and '직렬' not in jik: cur_jr,cur_ju=split_jik(jik)
        dae=g(i_dae).strip()
        if not dae or '구분' in dae: continue
        jg=g(i_jg).replace('\n','').replace(' ','') or '9급'
        out.append(["광주","교행",yr,rd,cur_g,"","",cur_jr,cur_ju,jg,daenorm(dae),
                    num(g(i_sel)),"","","","","","","",num(g(i_hap)),"",num(g(i_cut)),"","","","",fn,""])
    return out

def parse_hwpx(path):
    fn=os.path.basename(path); yr=yr_of(fn); rd=(re.search(r"제s*(d+)s*회",fn).group(1)+"회") if re.search(r"제s*(d+)s*회",fn) else "1회"
    try: t=H5.extract(path)
    except Exception:
        z=zipfile.ZipFile(path); secs=sorted(n for n in z.namelist() if re.search(r'section\d+\.xml$',n.lower()))
        t='\n'.join(re.sub('<[^>]+>','',x) for s in secs for x in re.findall(r'<hp:t>(.*?)</hp:t>',z.read(s).decode('utf-8','ignore'),flags=re.S))
    ls=[x.strip() for x in t.split('\n') if x.strip()]
    st=next((i for i,l in enumerate(ls) if l.replace(' ','')=='비고'),None)
    if st is None: return []
    toks=ls[st+1:]; out=[]; cur_g=cur_jr=cur_ju=''; buf=[]; i=0; n=len(toks)
    while i<n:
        tk=toks[i]
        if len(tk)>14 or '※' in tk or tk.startswith(('다.','2.','3.','○')): break
        if JG.match(tk.replace(' ','')):
            jg=tk.replace(' ','')
            dae=buf[-1] if buf else '일반'
            txts=[b for b in buf[:-1] if not re.match(r'^[\d,]+$',b.replace(' ',''))]
            for b in txts:
                gg=gub(b)
                if gg: cur_g=gg
            BAD=('과락','미달','합격','인원','경쟁','공개','경력','공채','경채','임용','시험')
            realtxt=[b for b in txts if not gub(b) and '제' not in b[:2] and not any(w in b for w in BAD)]
            if len(realtxt)>=2:
                cur_jr=re.sub(r'\s+','',realtxt[-2]).strip('()'); cur_ju=re.sub(r'\s+','',realtxt[-1]).strip('()')
                if cur_jr.endswith('직') and len(cur_jr)>1: cur_jr=cur_jr[:-1]
            elif len(realtxt)==1:
                cur_jr,cur_ju=split_jik(realtxt[-1])
            vals=toks[i+1:i+4]
            if len(vals)<3: break
            sel,hap,cut=vals
            out.append(["광주","교행",yr,rd,cur_g,"","",cur_jr,cur_ju,jg,daenorm(dae),
                        num(sel),"","","","","","","",num(hap),"",num(cut),"","","","",fn,""])
            i+=4; buf=[]; continue
        buf.append(tk); i+=1
    return out

if __name__=='__main__':
    out=[]
    for f in sorted(glob.glob(os.path.join(ROOT,'*.pdf'))):
        fn=os.path.basename(f)
        if '합격자' not in fn and '합격선' not in fn: continue
        if '응시' in fn or '접수' in fn: continue
        r=parse_pdf(f); print(f"{fn[:34]:34} -> {len(r)}"); out+=r
    for f in glob.glob(os.path.join(ROOT,'*.hwpx')):
        r=parse_hwpx(f); print(f"{os.path.basename(f)[:34]:34} -> {len(r)}"); out+=r
    OUT=os.path.join(os.path.dirname(__file__),'광주_교행.csv')
    with open(OUT,'w',encoding='utf-8-sig',newline='') as fp:
        w=csv.writer(fp); w.writerow(HEADERS); w.writerows(out)
    print('TOTAL',len(out))
    for r in out: print(r[2:12]+[r[19],r[21]])
