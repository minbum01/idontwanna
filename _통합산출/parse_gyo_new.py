# -*- coding: utf-8 -*-
"""교행 6지역 합격선: PDF(울산·충북·전북 지역별 컬럼설정) + hwp(대전·강원·충남 본문). 합격선 원본값, 기준 자동."""
import pdfplumber, re, os, glob, csv, importlib.util, zipfile
ROOT=r"C:/Users/admin/Documents/이민범 개발/합격선/합격선 최종모음"
HEADERS=["지역","시험종류","연도","회차","시험구분","임용예정기관","직군","직렬","직류","직급","대상",
         "선발예정인원","접수인원","접수여성","경쟁률(접수/선발)","응시인원","응시여성","응시율","경쟁률(응시/선발)",
         "필기합격인원","필기합격여성","합격선","양성평등성별","양성평등합격선","최종합격인원","최종합격여성",
         "원본파일명","비고"]
_h=importlib.util.spec_from_file_location('h',os.path.join(os.path.dirname(__file__),'hwp5_text.py'))
H5=importlib.util.module_from_spec(_h); _h.loader.exec_module(H5)

def daenorm(s):
    s=re.sub(r'\s+','',str(s))
    if '저소득' in s: return '저소득층'
    if '장애' in s: return '장애인'
    if '보훈' in s: return '보훈청추천'
    if '기술계' in s: return '기술계고'
    return s or '일반'
def split_jik(s):
    s=str(s).replace('\n','').strip()
    s=re.sub(r'\s*/\s*\d+급','',s)  # '교육행정/9급'
    m=re.match(r'^(.+?)\s*\((.+?)\)',s)
    if m: jr,ju=re.sub(r'\s+','',m.group(1)),re.sub(r'\s+','',m.group(2))
    else: jr=ju=re.sub(r'\s+','',s)
    if jr.endswith('직') and len(jr)>1: jr=jr[:-1]
    return jr,ju
def parse_cut(s):
    s=str(s).replace('\n','').strip()
    if s in ('','-','–','비공개'): return '',''
    m=re.match(r'^\s*([\d.]+)\s*[/(]\s*([\d.]+)', s)
    if m: return m.group(1), m.group(2)
    v=re.match(r'^\s*([\d.]+)', s)
    return (v.group(1) if v else ''),''
def gub(s):
    s=str(s).replace(' ','')
    if '공개' in s: return '공개경쟁'
    if '경력' in s: return '경력경쟁'
    return ''
def yr_rd(fn):
    y=re.search(r'(\d{4})',fn); r=re.search(r'제\s*(\d+)\s*회',fn)
    return (y.group(1) if y else ''),(r.group(1)+'회' if r else '2회')

# 지역별 컬럼 인덱스
CONF={'울산':dict(sigu=0,jik=1,dae=2,jg=3,sel=4,hap=5,cut=6),
      '충북':dict(sigu=0,jik=1,dae=2,jg=-1,sel=3,hap=4,cut=5),
      '전북':dict(sigu=-1,jik=0,dae=1,jg=-1,sel=2,hap=3,cut=4)}

def parse_pdf(path,region):
    fn=os.path.basename(path); yr,rd=yr_rd(fn); cf=CONF[region]
    out=[]
    with pdfplumber.open(path) as pdf:
        tabs=[p.extract_table() for p in pdf.pages]
    cur_g='공개경쟁'; cur_jr=cur_ju=''; cur_jg='9급'
    for t in tabs:
        if not t: continue
        if not any('합격' in str(c) for c in (t[0] or [])): continue
        for r in t[1:]:
            c=[(x or '') for x in r]
            def g(i): return c[i] if (0<=i<len(c)) else ''
            if cf['sigu']>=0 and gub(g(cf['sigu'])): cur_g=gub(g(cf['sigu']))
            jik=g(cf['jik']).replace('\n','').strip()
            if jik and not re.match(r'^\s*(계|합계|소계|총계)',jik) and '직렬' not in jik and '모집' not in jik:
                cur_jr,cur_ju=split_jik(jik);
                if gub(jik): continue
            if cf['jg']>=0:
                jgc=g(cf['jg']).replace(' ','').strip()
                if re.match(r'\d+급',jgc): cur_jg=jgc
            dae=daenorm(g(cf['dae'])) if cf['dae']>=0 else '일반'
            cut,avg=parse_cut(g(cf['cut']))
            hap=re.sub(r'[,\s]','',g(cf['hap']))
            if cut=='' and (hap in ('','0','-')): continue
            if not cur_jr: continue
            note=('평균%s'%avg) if avg else ''
            out.append([region,"교행",yr,rd,cur_g,"","",cur_jr,cur_ju,cur_jg,dae,
                        re.sub(r'[,\s]','',g(cf['sel'])),"","","","","","","",
                        hap if hap not in('-',) else "","",cut,"","","","",fn,note])
    return out

# ---- hwp 교행 (대전·강원·충남): 본문에서 합격선 표 토큰 파싱 ----
def hwp_text(path):
    try: return H5.extract(path)
    except Exception:
        z=zipfile.ZipFile(path); secs=sorted(n for n in z.namelist() if re.search(r'section\d+\.xml$',n.lower()))
        return '\n'.join(re.sub('<[^>]+>','',x) for s in secs for x in re.findall(r'<hp:t>(.*?)</hp:t>',z.read(s).decode('utf-8','ignore'),flags=re.S))

if __name__=='__main__':
    out=[]
    for folder,region in [('07 울산 교행','울산'),('10 충북 교행','충북'),('12 전북 교행','전북')]:
        for f in sorted(glob.glob(os.path.join(ROOT,folder,'*.pdf'))):
            fn=os.path.basename(f)
            if any(k in fn for k in ('접수','응시','원서','출원')) and '합격' not in fn: continue
            try:
                r=parse_pdf(f,region)
                if r: print(f"{region} {fn[:28]:28} -> {len(r)}"); out+=r
            except Exception as e: print(fn[:28],'ERR',e)
    OUT=os.path.join(os.path.dirname(__file__),'교행_신규pdf.csv')
    with open(OUT,'w',encoding='utf-8-sig',newline='') as fp:
        w=csv.writer(fp); w.writerow(HEADERS); w.writerows(out)
    from collections import Counter
    print('TOTAL',len(out),dict(Counter(r[0] for r in out)))
    for r in out[:10]: print(r[0],r[3],r[4],r[7],r[8],r[10],'선발',r[11],'합격',r[19],'합격선',r[21],r[27])
