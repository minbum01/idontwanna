# -*- coding: utf-8 -*-
"""접수현황(원서접수/출원) 파일을 읽어 합격선_통합_merged.csv의 빈 접수인원을 채움.
매칭: (지역,연도,직렬,직류,대상,임용기관) → 없으면 (…,대상) → (직렬,직류). pdf+hwp."""
import pdfplumber, re, os, glob, csv, importlib.util
BASE=r"C:/Users/admin/Documents/이민범 개발/합격선/합격선 최종모음"
MERGED=os.path.join(os.path.dirname(__file__),"합격선_통합_merged.csv")
_h=importlib.util.spec_from_file_location('h',os.path.join(os.path.dirname(__file__),'hwp5_text.py'))
H5=importlib.util.module_from_spec(_h); _h.loader.exec_module(H5)

def num(t):
    t=re.sub(r'[,\s명]','',str(t or ''))
    return '' if t in ('','-','–') else t
def daenorm(s):
    s=re.sub(r'\s+','',str(s))
    if '저소득' in s: return '저소득층'
    if '장애' in s: return '장애인'
    if '보훈' in s: return '보훈청추천'
    return s or '일반'
def parse_jik(s):
    s=str(s).replace('\n','').strip()
    m=re.match(r'^(\D+?)(\d+급|연구사|지도사)\s*\((.+?)\)\s*(.*)$', s)
    if m:
        jr,jg,inner,tail=m.group(1),m.group(2),m.group(3),m.group(4)
        ju,dae=(inner.rsplit('_',1) if '_' in inner else (inner,(tail or '일반')))
    else:
        m2=re.match(r'^(.+?)\s*\((.+?)\)\s*(.*)$',s)
        if m2: jr,ju,dae=m2.group(1),m2.group(2),(m2.group(3) or '일반')
        else: jr=ju=s; dae='일반'
    jr=re.sub(r'\s+','',jr); ju=re.sub(r'\s+','',ju)
    if jr.endswith('직') and len(jr)>1: jr=jr[:-1]
    return jr,ju,daenorm(dae)
def yr_of(fn,blob=''):
    for s in (fn,blob):
        m=re.search(r'(20\d{2})',s)
        if m: return m.group(1)
    return ''
def hidx(H,kw,*ex):
    for i,c in enumerate(H):
        cc=str(c or '').replace('\n','').replace(' ','')
        if kw in cc and not any(e in cc for e in ex): return i
    return -1

def tables(path):
    out=[]
    with pdfplumber.open(path) as pdf:
        for p in pdf.pages:
            t=p.extract_table()
            if t: out.append(t)
    return out

JG=re.compile(r'^(\d+급|연구사|지도사)$')
def isnum(t):
    t=t.replace(',','').replace(' ',''); return bool(re.match(r'^\d+(\.\d+)?$',t))
def hwp_pairs(path, region):
    """hwp 접수표(직렬/직류/직급/선발/접수/경쟁률 계열)에서 (지역,연도,직렬,직류,대상)->접수 산출"""
    out=[]
    txt=H5.extract(path); yr=yr_of(os.path.basename(path),txt)
    toks=[x.strip() for x in txt.split('\n') if x.strip()]
    # 헤더 위치
    hi=next((i for i,l in enumerate(toks) if l.replace(' ','') in ('접수인원','출원인원')), None)
    if hi is None: return out
    i=hi+1; n=len(toks); cur_jr=cur_ju=''; buf=[]
    while i<n:
        t=toks[i]; nm=t.replace(' ','')
        if len(t)>16 or '※' in t or '경쟁률' in t and i>hi+10:
            if len(t)>16 or '※' in t: break
        if JG.match(nm):
            txts=[b for b in buf if not isnum(b.replace(',','')) and ':' not in b]
            if len(txts)>=2: cur_jr,cur_ju=re.sub(r'\s+','',txts[-2]),re.sub(r'\s+','',txts[-1])
            elif len(txts)==1: cur_jr=cur_ju=re.sub(r'\s+','',txts[-1])
            if cur_jr.endswith('직') and len(cur_jr)>1: cur_jr=cur_jr[:-1]
            # 직급 다음: 선발, 접수
            vals=[v for v in toks[i+1:i+4] if isnum(v.replace(',',''))]
            if len(vals)>=2:
                out.append((region,yr,cur_jr,cur_ju,'일반', num(vals[1])))
            i+=1; buf=[]; continue
        buf.append(t); i+=1
    return out

def build_lookup():
    lut={}; lut2={}
    for folder in sorted(os.listdir(BASE)):
        p=os.path.join(BASE,folder)
        if not os.path.isdir(p): continue
        m=re.match(r'\d+\s*(\S+)\s*(공무원|교행)',folder)
        if not m: continue
        region=m.group(1)
        for f in glob.glob(os.path.join(p,'*.pdf')):
            fn=os.path.basename(f)
            if not any(k in fn for k in ('접수','원서','출원')) or '합격' in fn or '2026' in fn: continue
            tbs=tables(f)
            if not tbs: continue
            for t in tbs:
                if not t or len(t)<2: continue
                H=t[0]
                i_jik=hidx(H,'직렬'); i_gig=hidx(H,'임용') if hidx(H,'임용')>=0 else hidx(H,'기관')
                i_jeop=hidx(H,'접수') if hidx(H,'접수')>=0 else (hidx(H,'출원') if hidx(H,'출원')>=0 else hidx(H,'원서'))
                if i_jik<0 or i_jeop<0: continue
                yr=yr_of(fn)
                cur=None
                for r in t[1:]:
                    c=[('' if x is None else x) for x in r]
                    jik=str(c[i_jik] if i_jik<len(c) else '').strip()
                    if jik and not re.match(r'^\s*(계|소계|총계|합계|구분)',jik) and '직렬' not in jik:
                        cur=parse_jik(jik)
                    if not cur: continue
                    gig=re.sub(r'\s+','',str(c[i_gig])) if (i_gig>=0 and i_gig<len(c)) else ''
                    if gig in ('소계','총계','계','합계'): continue
                    jp=num(c[i_jeop] if i_jeop<len(c) else '')
                    if not jp: continue
                    jr,ju,dae=cur
                    if gig: lut[(region,yr,jr,ju,dae,gig)]=jp
                    lut.setdefault((region,yr,jr,ju,dae),jp)
                    lut2.setdefault((region,yr,jr,ju),jp)
        # hwp/hwpx 접수
        for f in glob.glob(os.path.join(p,'*.hwp'))+glob.glob(os.path.join(p,'*.hwpx')):
            fn=os.path.basename(f)
            if not any(k in fn for k in ('접수','원서','출원')) or '합격' in fn or '2026' in fn: continue
            try:
                for (rg,yr,jr,ju,dae,jp) in hwp_pairs(f,region):
                    if jp:
                        lut.setdefault((rg,yr,jr,ju,dae),jp); lut2.setdefault((rg,yr,jr,ju),jp)
            except Exception: pass
    return lut,lut2

def main():
    lut,lut2=build_lookup()
    print('접수 lookup:',len(lut))
    with open(MERGED,encoding='utf-8-sig') as fp:
        rows=list(csv.reader(fp)); Hd=rows[0]; data=rows[1:]
    I={h:i for i,h in enumerate(Hd)}
    filled=0
    for r in data:
        if r[I['접수인원']].strip(): continue
        reg,yr,jr,ju,dae,gig=r[I['지역']],r[I['연도']],r[I['직렬']],r[I['직류']],r[I['대상']],re.sub(r'\s+','',r[I['임용예정기관']])
        v=lut.get((reg,yr,jr,ju,dae,gig)) or lut.get((reg,yr,jr,ju,dae)) or lut2.get((reg,yr,jr,ju))
        if v: r[I['접수인원']]=v; filled+=1
    with open(MERGED,'w',encoding='utf-8-sig',newline='') as fp:
        w=csv.writer(fp); w.writerow(Hd); w.writerows(data)
    print('접수 채운 행:',filled)

if __name__=='__main__':
    main()
