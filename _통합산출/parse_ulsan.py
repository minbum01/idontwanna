# -*- coding: utf-8 -*-
"""울산 공무원 합격선 pdf(직렬(직류)/대상/직급/선발/합격/합격선/양성) -> 통일 양식. 과목평균."""
import pdfplumber, re, os, glob, csv
ROOT=r"C:/Users/admin/Documents/이민범 개발/합격선/합격선 최종모음/07 울산 공무원"
HEADERS=["지역","시험종류","연도","회차","시험구분","임용예정기관","직군","직렬","직류","직급","대상",
         "선발예정인원","접수인원","접수여성","경쟁률(접수/선발)","응시인원","응시여성","응시율","경쟁률(응시/선발)",
         "필기합격인원","필기합격여성","합격선","양성평등성별","양성평등합격선","최종합격인원","최종합격여성",
         "원본파일명","비고"]
def num(t):
    t=re.sub(r'[,\s점]','',str(t or ''))
    return '' if t in ('','-','–','비공개') else t
def daenorm(s):
    s=re.sub(r'\s+','',str(s))
    if '저소득' in s: return '저소득층'
    if '장애' in s: return '장애인'
    if '보훈' in s: return '보훈청추천'
    return s or '일반'
def split_jik(s):
    s=str(s).replace('\n','').strip()
    m=re.match(r'^(.+?)\s*\((.+?)\)',s)
    if m: jr,ju=re.sub(r'\s+','',m.group(1)),re.sub(r'\s+','',m.group(2))
    else: jr=ju=re.sub(r'\s+','',s)
    if jr.endswith('직') and len(jr)>1: jr=jr[:-1]
    return jr,ju
def yr_rd(fn):
    y=re.search(r'(\d{4})',fn); r=re.search(r'제\s*(\d+)\s*회',fn)
    return (y.group(1) if y else ''),(r.group(1)+'회' if r else '')

def parse(path):
    fn=os.path.basename(path); yr,rd=yr_rd(fn)
    with pdfplumber.open(path) as pdf:
        tabs=[p.extract_table() for p in pdf.pages]
    out=[]
    for t in tabs:
        if not t or len(t)<2: continue
        H=[ (c or '').replace('\n','').replace(' ','') for c in t[0]]
        def idx(kw,*ex):
            for i,c in enumerate(H):
                if kw in c and not any(e in c for e in ex): return i
            return -1
        i_jik=idx('직렬'); i_dae=idx('구분') if idx('구분')>=0 else (i_jik+1 if i_jik>=0 else -1)
        i_jg=idx('직급'); i_sel=idx('선발'); i_hap=idx('필기',) ; i_cut=idx('합격선','양성'); i_yang=idx('양성')
        if i_hap<0: i_hap=idx('합격인원')
        if i_jik<0 or i_sel<0 or i_cut<0: continue
        cur_jr=cur_ju=''
        for r in t[1:]:
            c=[(x or '') for x in r]
            def g(i): return c[i] if 0<=i<len(c) else ''
            jikraw=g(i_jik).replace('\n','').strip()
            if '직렬' in jikraw or re.match(r'^\s*계',jikraw) or '개직렬' in jikraw.replace(' ',''): continue
            if jikraw and '소계' not in jikraw: cur_jr,cur_ju=split_jik(jikraw)
            dae=g(i_dae).strip()
            if not dae or '구분' in dae or '소계' in dae: continue
            sigu='공개경쟁'; dn=daenorm(dae)
            if dn in ('공개경쟁','경력경쟁'): sigu=dn; dn='일반'
            cut=num(g(i_cut))
            out.append(["울산","공무원",yr,rd or "1회",sigu,"","",cur_jr,cur_ju,
                        g(i_jg).replace(' ','').strip() or "9급",dn,
                        num(g(i_sel)),"","","","","","","",num(g(i_hap)),"",cut,"",num(g(i_yang)) if i_yang>=0 else "","","",fn,""])
    return out

if __name__=='__main__':
    out=[]
    for f in sorted(glob.glob(os.path.join(ROOT,'*.pdf'))):
        if '합격선' not in os.path.basename(f): continue
        r=parse(f); print(os.path.basename(f)[:34],'->',len(r)); out+=r
    OUT=os.path.join(os.path.dirname(__file__),'울산_공무원.csv')
    with open(OUT,'w',encoding='utf-8-sig',newline='') as fp:
        w=csv.writer(fp); w.writerow(HEADERS); w.writerows(out)
    print('TOTAL',len(out))
    for r in out[:8]: print(r[2:12]+[r[19],r[21],r[23]])
