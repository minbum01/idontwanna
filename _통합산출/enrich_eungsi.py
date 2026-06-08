# -*- coding: utf-8 -*-
"""교행 응시현황(서울·부산)에서 선발/접수/응시를 읽어 교행_data.csv의 빈칸 보강.
매칭키: (지역,연도,직렬,직류,대상) → 없으면 (지역,연도,직렬,대상) 폴백."""
import pdfplumber, glob, os, re, csv
BASE=r"C:/Users/admin/Documents/이민범 개발/합격선/합격선 최종모음"
DATA=os.path.join(os.path.dirname(__file__),"교행_data.csv")
DAES={"일반","장애","장애인","저소득","저소득층","소계","보훈청추천","공통"}

def daenorm(s):
    s=re.sub(r'\s+','',s)
    if '저소득' in s: return '저소득층'
    if '장애' in s: return '장애인'
    if '보훈' in s: return '보훈청추천'
    if '소계' in s: return '소계'
    return s or '일반'

def num(t):
    t=re.sub(r'[,\s명]','',str(t or ''))
    return '' if t in ('','-','–') else t

def split_busan(name):
    """'교육행정(일반)'→(교육행정,교육행정,일반) / '공업(일반기계)'→(공업,일반기계,일반)"""
    s=name.strip()
    m=re.match(r'^(.+?)\s*\((.+?)\)\s*$', s)
    if not m: return (re.sub(r'\s+','',s), re.sub(r'\s+','',s), '일반')
    a=re.sub(r'\s+','',m.group(1)); b=re.sub(r'\s+','',m.group(2))
    if a.endswith('직') and len(a)>1: a=a[:-1]
    if b.replace(' ','') in DAES or daenorm(b) in ('장애인','저소득층','보훈청추천','소계') or b in ('일반',):
        return (a,a,daenorm(b))
    return (a,b,'일반')

def split_seoul(jikryu_dae):
    """('교육행정','일 반') 또는 ('공업(일반기계)','일 반')"""
    name,dae = jikryu_dae
    name=name.strip()
    m=re.match(r'^(.+?)\s*\((.+?)\)\s*$', name)
    if m:
        a=re.sub(r'\s+','',m.group(1)); b=re.sub(r'\s+','',m.group(2))
    else:
        a=re.sub(r'\s+','',name); b=a
    if a.endswith('직') and len(a)>1: a=a[:-1]
    return (a,b,daenorm(dae))

def yr_of(fn):
    m=re.search(r'(\d{4})',fn); return m.group(1) if m else ''

def hidx(header, *kw_excl):
    """헤더에서 키워드 포함 & 제외어 없는 컬럼 인덱스"""
    kw=kw_excl[0]; excl=kw_excl[1:]
    for i,c in enumerate(header):
        cc=(c or '').replace('\n','').replace(' ','')
        if kw in cc and not any(e in cc for e in excl): return i
    return -1

def build_lookup():
    lut={}; lut2={}
    for folder,region in [("01 서울 교행","서울"),("02 부산 교행","부산"),("04 인천 교행","인천"),("05 광주 교행","광주")]:
        for f in glob.glob(os.path.join(BASE,folder,"*.pdf")):
            fn=os.path.basename(f)
            if not any(k in fn for k in ("응시현황","응시 현황","응시율","접수결과","접수 결과")): continue
            yr=yr_of(fn)
            try:
                with pdfplumber.open(f) as pdf:
                    t=pdf.pages[0].extract_table()
            except: t=None
            if not t or len(t)<2: continue
            header=t[0]
            seoul = hidx(header,'선발구분')>=0
            incheon = (not seoul) and hidx(header,'직류')>=0 and hidx(header,'구분')>=0
            busan = (not seoul) and (not incheon) and (hidx(header,'응시직렬')>=0 or hidx(header,'직렬')>=0)
            i_sel=hidx(header,'선발','구분'); i_jeop=hidx(header,'접수')
            if i_jeop<0: i_jeop=hidx(header,'지원')
            i_eung=hidx(header,'응시','율','직렬','접수')
            if i_sel<0 or i_jeop<0:
                print('   [skip 컬럼탐지실패]',fn[:30]); continue
            if seoul:
                i_name=hidx(header,'직렬'); i_dae=hidx(header,'선발구분')
                cur_name=''
                for r in t[1:]:
                    c=[(x or '') for x in r]
                    name=(c[i_name] if i_name<len(c) else '').strip()
                    if name and '소계' not in name and '합계' not in name: cur_name=name
                    dae=(c[i_dae] if i_dae<len(c) else '').strip()
                    if not dae or '소계' in name or '합계' in (name+dae): continue
                    jr,ju,ds=split_seoul((cur_name,dae))
                    if ds=='소계': continue
                    key=(region,yr,jr,ju,ds)
                    lut[key]=(num(c[i_sel]),num(c[i_jeop]),num(c[i_eung]))
                    lut2.setdefault((region,yr,jr,ds),[]).append(lut[key])
            elif busan:
                i_name=hidx(header,'응시직렬')
                if i_name<0: i_name=hidx(header,'직렬')
                for r in t[1:]:
                    c=[(x or '') for x in r]
                    name=(c[i_name] if i_name<len(c) else '').strip()
                    if not name or '소계' in name or '총계' in name or '합계' in name: continue
                    jr,ju,ds=split_busan(name)
                    if ds=='소계': continue
                    key=(region,yr,jr,ju,ds)
                    lut[key]=(num(c[i_sel]),num(c[i_jeop]),num(c[i_eung]))
                    lut2.setdefault((region,yr,jr,ds),[]).append(lut[key])
            elif incheon:
                i_jik=hidx(header,'직렬'); i_ju=hidx(header,'직류'); i_dae=hidx(header,'구분','시험')
                combined=(i_jik==i_ju)   # '직렬(직류)' 한 칸
                cur_jr=cur_ju=''
                for r in t[1:]:
                    c=[(x or '') for x in r]
                    raw=(c[i_jik] if i_jik<len(c) else '').strip()
                    dae=(c[i_dae] if i_dae<len(c) else '').strip()
                    if raw and '소계' not in raw and '계' not in raw.replace(' ',''):
                        if combined:
                            cur_jr,cur_ju=split_busan(raw)[:2]
                        else:
                            cur_jr=re.sub(r'\s+','',raw)
                            cur_ju=re.sub(r'\s+','',(c[i_ju] if i_ju<len(c) else '') )
                            if cur_jr.endswith('직') and len(cur_jr)>1: cur_jr=cur_jr[:-1]
                    if not dae or '소계' in dae or '계' in dae.replace(' ',''): continue
                    ds=daenorm(dae)
                    key=(region,yr,cur_jr,cur_ju,ds)
                    lut[key]=(num(c[i_sel]),num(c[i_jeop]),num(c[i_eung]) if i_eung>=0 else '')
                    lut2.setdefault((region,yr,cur_jr,ds),[]).append(lut[key])
            else:
                print('   [skip 양식미상]',fn[:30])
    return lut,lut2

def enrich_csv(path,lut,lut2):
    with open(path,encoding='utf-8-sig') as fp:
        rows=list(csv.reader(fp)); H=rows[0]; data=rows[1:]
    I={h:i for i,h in enumerate(H)}
    filled=0
    for r in data:
        if (r[I['접수인원']].strip() or r[I['응시인원']].strip()): continue
        k=(r[I['지역']],r[I['연도']],r[I['직렬']],r[I['직류']],r[I['대상']])
        v=lut.get(k)
        if not v:
            cand=lut2.get((r[I['지역']],r[I['연도']],r[I['직렬']],r[I['대상']]))
            v=cand[0] if cand and len(cand)==1 else None
        if not v: continue
        sel,jeop,eung=v
        if sel and not r[I['선발예정인원']].strip(): r[I['선발예정인원']]=sel
        if jeop: r[I['접수인원']]=jeop
        if eung: r[I['응시인원']]=eung
        filled+=1
    with open(path,'w',encoding='utf-8-sig',newline='') as fp:
        w=csv.writer(fp); w.writerow(H); w.writerows(data)
    return filled,len(data)

def main():
    lut,lut2=build_lookup()
    print('lookup keys:',len(lut))
    for fn in ['교행_data.csv','광주_교행.csv']:
        p=os.path.join(os.path.dirname(__file__),fn)
        if not os.path.exists(p): continue
        f,t=enrich_csv(p,lut,lut2)
        print(f'보강 {fn}: {f}/{t}')

if __name__=='__main__':
    main()
