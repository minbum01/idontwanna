# -*- coding: utf-8 -*-
"""인천 공무원 통계자료(9급·7급) -> 통일 양식. 합격선=평균(총점은 비고). 임용예정기관 보존.
직렬(류) 예: '행정9급(일반행정_일반)' = 직렬+직급+(직류_대상). 시험구분 원본미표기→공개경쟁 가정."""
import pdfplumber, re, os, glob, csv
ROOT=r"C:/Users/admin/Documents/이민범 개발/합격선/합격선 최종모음"
HEADERS=["지역","시험종류","연도","회차","시험구분","임용예정기관","직군","직렬","직류","직급","대상",
         "선발예정인원","접수인원","접수여성","경쟁률(접수/선발)","응시인원","응시여성","응시율","경쟁률(응시/선발)",
         "필기합격인원","필기합격여성","합격선","양성평등성별","양성평등합격선","최종합격인원","최종합격여성",
         "원본파일명","비고"]

def num(t):
    t=re.sub(r'[,\s명]','',str(t or ''))
    return '' if t in ('','-','–','0') else t

def num0(t):  # 0 허용(선발/합격)
    t=re.sub(r'[,\s명]','',str(t or ''))
    return '' if t in ('','-','–') else t

def daenorm(s):
    s=re.sub(r'\s+','',s)
    if '저소득' in s: return '저소득층'
    if '장애' in s: return '장애인'
    if '보훈' in s: return '보훈청추천'
    return s or '일반'

def parse_jik(s):
    s=s.replace('\n','').strip()
    m=re.match(r'^(\D+?)(\d+급)\((.+)\)$', s)
    if not m:
        return (re.sub(r'\s+','',s), re.sub(r'\s+','',s), '', '일반')
    jr=m.group(1).strip(); jg=m.group(2); inner=m.group(3)
    if '_' in inner:
        ju,dae=inner.rsplit('_',1); ju=ju.strip(); dae=daenorm(dae)
    else:
        ju=inner.strip(); dae='일반'
    if jr.endswith('직') and len(jr)>1: jr=jr[:-1]
    return jr,ju,jg,dae

def yr_of(fn):
    m=re.search(r'(\d{4})',fn); return m.group(1) if m else ''

def hidx(header,*kw):
    want=kw[0]; excl=kw[1:]
    for i,c in enumerate(header):
        cc=(c or '').replace('\n','').replace(' ','')
        if want in cc and not any(e in cc for e in excl): return i
    return -1

def parse_file(path):
    fn=os.path.basename(path); yr=yr_of(fn)
    with pdfplumber.open(path) as pdf:
        tabs=[p.extract_table() for p in pdf.pages]
    # 헤더 인덱스: 헤더 있는 첫 표에서 한 번만 정함
    idx=None
    for t in tabs:
        if not t: continue
        H=t[0]
        ij=hidx(H,'직렬'); isel=hidx(H,'선발예정'); icutA=hidx(H,'합격선','총점')
        if ij>=0 and isel>=0 and icutA>=0:
            idx=dict(jik=ij,gig=hidx(H,'임용'),sel=isel,chul=hidx(H,'출원'),
                     eung=hidx(H,'응시','율'),hap=hidx(H,'필기합격','선'),
                     cutT=hidx(H,'총점'),cutA=icutA,fin=hidx(H,'최종합격'))
            break
    if not idx: return []
    def g(c,i): return c[i] if (i is not None and 0<=i<len(c)) else ''
    out=[]
    for t in tabs:
        if not t: continue
        i_jik,i_gig,i_sel=idx['jik'],idx['gig'],idx['sel']
        i_chul,i_eung,i_hap=idx['chul'],idx['eung'],idx['hap']
        i_cutT,i_cutA,i_fin=idx['cutT'],idx['cutA'],idx['fin']
        for r in t:
            c=[(x or '') for x in r]
            jik=g(c,i_jik); j=jik.replace('\n','').replace(' ','')
            if not j or '직렬' in j or '(' not in jik: continue
            jr,ju,jg,dae=parse_jik(jik)
            cut=num(g(c,i_cutA))
            note=('총점%s'%num0(g(c,i_cutT))) if i_cutT>=0 and num0(g(c,i_cutT)) else ''
            fin=num0(g(c,i_fin)) if i_fin>=0 else ''
            out.append(["인천","공무원",yr,"","공개경쟁",g(c,i_gig).replace('\n',' ').strip(),"",jr,ju,jg,dae,
                        num0(g(c,i_sel)),num0(g(c,i_chul)),"","",num0(g(c,i_eung)),"","","",num0(g(c,i_hap)),"",cut,"","",fin,"",fn,note])
    return out

if __name__=='__main__':
    out=[]
    for f in sorted(glob.glob(os.path.join(ROOT,'04 인천 공무원','*.pdf'))):
        fn=os.path.basename(f)
        if '2026' in fn: continue   # 접수단계 별도(시트3)
        try:
            r=parse_file(f); print(f"{fn[:40]:40} -> {len(r)}"); out+=r
        except Exception as e: print(fn,'ERR',e)
    OUT=os.path.join(os.path.dirname(__file__),'인천_공무원.csv')
    with open(OUT,'w',encoding='utf-8-sig',newline='') as fp:
        w=csv.writer(fp); w.writerow(HEADERS); w.writerows(out)
    print('TOTAL',len(out))
    for r in out[:6]: print(r[5:12]+[r[19],r[21],r[27]])
