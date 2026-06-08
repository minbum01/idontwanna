# -*- coding: utf-8 -*-
"""광주 공무원 합격자공고 hwp/hwpx(배포용 아님) BodyText -> 통일 양식.
표: 직렬(직류)/구분(대상)/직급/선발/응시/합격/합격선(양성). 합격선=과목평균. 출원 없음.
시험구분 원본미표기→공개경쟁 가정."""
import re, os, glob, csv, importlib.util, zipfile
ROOT=r"C:/Users/admin/Documents/이민범 개발/합격선/합격선 최종모음"
HEADERS=["지역","시험종류","연도","회차","시험구분","임용예정기관","직군","직렬","직류","직급","대상",
         "선발예정인원","접수인원","접수여성","경쟁률(접수/선발)","응시인원","응시여성","응시율","경쟁률(응시/선발)",
         "필기합격인원","필기합격여성","합격선","양성평등성별","양성평등합격선","최종합격인원","최종합격여성",
         "원본파일명","비고"]
_h=importlib.util.spec_from_file_location('h',os.path.join(os.path.dirname(__file__),'hwp5_text.py'))
H5=importlib.util.module_from_spec(_h); _h.loader.exec_module(H5)

JG=re.compile(r'^(\d+급|연구사|지도사|연구관)$')
def is_num(t):
    t=t.replace(',','').replace(' ','')
    return bool(re.match(r'^\d+(\.\d+)?$',t)) or t in ('-','–')
def daenorm(s):
    s=re.sub(r'\s+','',s)
    if '저소득' in s: return '저소득층'
    if '장애' in s: return '장애인'
    if '보훈' in s: return '보훈청추천'
    if '지방의회' in s: return '지방의회'
    return s or '일반'
def num(t):
    t=str(t).replace(',','').replace(' ','').strip()
    return '' if t in ('','-','–') else t
def clean(s): return re.sub(r'\s+','',s).strip('()')

def hwpx_text(path):
    z=zipfile.ZipFile(path)
    secs=[n for n in z.namelist() if re.search(r'section\d+\.xml$',n.lower())]
    out=[]
    for s in sorted(secs):
        xml=z.read(s).decode('utf-8','ignore')
        # <hp:t>...</hp:t> 텍스트
        out+=re.findall(r'<hp:t>(.*?)</hp:t>', xml, flags=re.S)
    return '\n'.join(re.sub(r'<[^>]+>','',x) for x in out)

def get_text(path):
    try: return H5.extract(path)       # hwp/hwpx(OLE2 배포본)
    except Exception:
        return hwpx_text(path)          # hwpx(OWPML zip)

def parse(path, yr, rd, region="광주"):
    t=get_text(path)
    lines=[x.strip() for x in t.split('\n') if x.strip()]
    # 표 시작: '합격선' 헤더 토큰 이후
    st=None
    for i,l in enumerate(lines):
        if l.replace(' ','').startswith('합격선') and ('양성' in l or '점' in l or '총점' in l or l.replace(' ','')=='합격선'):
            st=i+1; break
    if st is None: return []
    toks=lines[st:]
    out=[]; cur_jr=cur_ju=''; buf=[]; i=0; n=len(toks)
    def endish(s):
        s2=s.replace(' ','')
        return (len(s)>14 or '※' in s or s.startswith(('다.','라.','마.','2.','3.','4.','○','-'))) and not JG.match(s2)
    while i<n:
        tk=toks[i]
        if endish(tk): break
        if JG.match(tk.replace(' ','')):
            jg=tk.replace(' ','')
            dae=buf[-1] if buf else '일반'
            txts=[b for b in buf[:-1] if not is_num(b)]
            # 직렬/직류 갱신: 텍스트가 2개면 직렬+직류
            if len(txts)>=2:
                cur_jr=clean(txts[-2]); cur_ju=clean(txts[-1])
            elif len(txts)==1:
                cur_jr=clean(txts[-1]); cur_ju=cur_jr
            vals=toks[i+1:i+5]
            if len(vals)<4: break
            sel,eung,hap,cut=vals
            m=re.match(r'^\s*([\d.]+)\s*\(\s*([\d.]+)\s*\)', cut)
            if m: cutv, yangs = m.group(1), m.group(2)
            else: cutv, yangs = num(cut), ''
            out.append([region,"공무원",yr,rd,"공개경쟁","","",cur_jr,cur_ju,jg,daenorm(dae),
                        num(sel),"","","",num(eung),"","","",num(hap),"",cutv,"",yangs,"","",os.path.basename(path),
                        "시험구분 원본미표기(공개로 가정)"])
            i+=5; buf=[]
            continue
        buf.append(tk); i+=1
    return out

def yr_rd(fn):
    y=re.search(r'(\d{4})',fn); r=re.search(r'제\s*(\d+)\s*회',fn)
    return (y.group(1) if y else ''),(r.group(1)+'회' if r else '')

if __name__=='__main__':
    out=[]
    for folder,region in [('05 광주 공무원','광주'),('06 대전 공무원','대전')]:
        for f in sorted(glob.glob(os.path.join(ROOT,folder,'*.hwp'))+glob.glob(os.path.join(ROOT,folder,'*.hwpx'))):
            fn=os.path.basename(f)
            if '합격' not in fn or '접수' in fn or '현황' in fn: continue
            yr,rd=yr_rd(fn)
            try:
                r=parse(f,yr,rd,region); print(f"{region} {fn[:30]:30} -> {len(r)}"); out+=r
            except Exception as e: print(fn[:30],'ERR',e)
    OUT=os.path.join(os.path.dirname(__file__),'광주_대전_공무원.csv')
    with open(OUT,'w',encoding='utf-8-sig',newline='') as fp:
        w=csv.writer(fp); w.writerow(HEADERS); w.writerows(out)
    print('TOTAL',len(out))
    for r in out[:8]: print(r[3:12]+[r[15],r[19],r[21],r[23]])
