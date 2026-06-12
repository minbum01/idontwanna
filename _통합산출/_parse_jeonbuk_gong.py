# -*- coding: utf-8 -*-
import re, csv, sys

BASE = r'C:/Users/admin/Documents/이민범 개발/합격선/합격선 최종모음/12 전북 공무원'
AP = open(BASE+'/전북공무원응시현황.md', encoding='utf-8').read().split('\n')
HP = open(BASE+'/전북공무원합격선.md', encoding='utf-8').read().split('\n')

def norm_target(s):
    if s is None: return '일반'
    s = s.strip()
    if '장애' in s: return '장애인'
    if '저소득' in s: return '저소득층'
    if s in ('의회','도·시군','시·군','도','도시군'): return '일반'
    return '일반'

def nk(o):
    o = o.replace(' ', '')
    o = o.replace('전라북도', '전북특별자치도')
    o = o.replace('도일괄', '전북특별자치도')
    return o

def store_org(o):
    o = o.strip().replace(' ', '')
    if o == '도일괄': return '전북특별자치도'
    return o

# 직렬 급 (직류[ : 대상])  콜론이 괄호 안 또는 괄호 뒤(:대상) 양쪽 모두 처리
PACK = re.compile(r'^([가-힣]+?)(\d+급)\(([^)]+)\)\s*(?::\s*([가-힣·]+))?(.*)$')
def parse_pack(line):
    m = PACK.match(line)
    if not m: return None
    jr, gd, inner, tgt_after, rest = m.groups()
    if ':' in inner:
        a, b = inner.split(':', 1)
        jl = a.strip(); tgt = norm_target(b)
    else:
        jl = inner.strip()
        tgt = norm_target(tgt_after) if tgt_after else '일반'
    return jr, gd, jl, tgt, rest.strip()

ISNUM = re.compile(r'^-?$|^\d')

# ---------- 응시현황 파싱 ----------
ATT = {}  # key -> dict
def addatt(year, hoe, jr, gd, jl, tgt, org, sel, app, exam, rate, comp, memo=''):
    key = (year, jl, tgt, nk(org))
    ATT[key] = dict(year=year, hoe=hoe, jr=jr, gd=gd, jl=jl, tgt=tgt,
                    org=store_org(org), sel=sel, app=app, exam=exam,
                    rate=rate, comp=comp, memo=memo)

year=None; hoe=None; cur=None  # cur=(jr,gd,jl,tgt)
for ln in AP:
    s = ln.strip()
    if not s: continue
    if s in ('23','24','25'):
        year = 2000+int(s); hoe='3회'; cur=None; continue
    if '필기시험' in s and ('응시현황' in s or '응시 현황' in s):
        cur=None; continue
    if s.startswith('시험직렬') or s.startswith('직급(') or s.startswith('직급('):
        continue
    if s.startswith('직급'):  # 2025 header "직급(직류) 임용기관..."
        continue
    if s.startswith('합격선') or s.startswith('양성초과') or s.startswith('(양성'):
        continue
    toks = s.split()
    pk = parse_pack(s)
    if pk:
        jr, gd, jl, tgt, rest = pk
        cur = [jr, gd, jl, tgt]
        rest = rest.strip()
        if not rest:
            continue
        # rest may be "계 ..." / "소계 ..." / "기관 nums" / "[bracket]..."
        s2 = rest
        toks = s2.split()
    else:
        s2 = s
    # bracket handling (2025)
    if s2.startswith('['):
        m = re.match(r'^\[([^\]]+)\](.*)$', s2)
        btxt, rem = m.group(1), m.group(2).strip()
        if cur is None: continue
        cur[3] = norm_target(btxt)
        if not rem:
            continue
        s2 = rem
        toks = s2.split()
    else:
        toks = s2.split()
    if not toks: continue
    if toks[0] in ('계','소계','총계'): continue
    if cur is None: continue
    jr, gd, jl, tgt = cur
    # find first numeric token => 기관 = tokens before it
    i = 0
    while i < len(toks) and not ISNUM.match(toks[i]):
        i += 1
    if i == 0:
        # token0 not numeric but maybe 기관 then nums; ISNUM matched? ensure
        i = 1
    org = ''.join(toks[:i])
    nums = toks[i:]
    if org in ('계','소계','총계',''): continue
    def gv(x):
        return '' if x in ('-','') else x
    if year in (2023,2024):
        # 선발 접수 응시 응시율% 경쟁률
        sel = gv(nums[0]) if len(nums)>0 else ''
        app = gv(nums[1]) if len(nums)>1 else ''
        exam= gv(nums[2]) if len(nums)>2 else ''
        rate= gv(nums[3].rstrip('%')) if len(nums)>3 else ''
        comp= gv(nums[4]) if len(nums)>4 else ''
    else:  # 2025: 선발 출원 경쟁률(x:1) 응시 응시율%
        sel = gv(nums[0]) if len(nums)>0 else ''
        app = gv(nums[1]) if len(nums)>1 else ''
        compraw = nums[2] if len(nums)>2 else ''
        exam= gv(nums[3]) if len(nums)>3 else ''
        rate= gv(nums[4].rstrip('%')) if len(nums)>4 else ''
        comp= ''
        if ':' in str(compraw):
            comp = compraw.split(':')[0]
        else:
            comp = gv(compraw)
    memo = ''
    if '없음' in s2: memo='출원자없음'
    addatt(year, hoe, jr, gd, jl, tgt, org, sel, app, exam, rate, comp, memo)

# ---------- 합격선 파싱 ----------
CUT = {}  # key -> (합격선, 양성, 필기합격)
def addcut(year, jl, tgt, org, cut, yang, pass_):
    CUT[(year, jl, tgt, nk(org))] = (cut, yang, pass_)

def clean_cut(v):
    if v in ('-','0','',None): return ''
    return v

year=None; cur=None
PACK2024 = re.compile(r'^([가-힣]+?)(\d+급)(?:\((장애인|저소득층|장애)\))?$')
for ln in HP:
    s = ln.strip()
    if not s: continue
    if s in ('23','24','25'):
        year=2000+int(s); cur=None; continue
    if '필기시험' in s and ('합격선' in s):
        cur=None; continue
    if s.startswith('시험직렬') or s.startswith('직렬명') or s.startswith('직급'):
        continue
    if s.startswith('합격선') or s.startswith('양성초과') or s.startswith('(양성') or s.startswith('※'):
        continue
    if s in ('합격인원','비고','계'):
        continue
    toks = s.split()
    if year in (2023,2025):
        pk = parse_pack(toks[0]) if PACK.match(toks[0]) else None
        # packing may span: e.g. "행정9급(일반행정): 장애인 소계 37 10"
        m2 = re.match(r'^([가-힣]+?)(\d+급)\(([^)]+)\)\s*(?::\s*([가-힣·]+))?\s*(.*)$', s)
        if m2:
            jr, gd, inner, suf, rest = m2.groups()
            if ':' in inner:
                a, b = inner.split(':', 1)
                jl = a.strip(); tgt = norm_target(b)
            else:
                jl = inner.strip()
                tgt = norm_target(suf) if suf else '일반'
            cur = (jl, tgt)
            # rest like "계 19 24" or "소계 37 10" -> skip data (it's totals)
            continue
        # sub-row: 기관 선발 합격 합격선 [양성합격인원 양성합격선]
        if toks[0] in ('계','소계','총계'): continue
        if cur is None: continue
        jl, tgt = cur
        i=0
        while i<len(toks) and not ISNUM.match(toks[i]): i+=1
        if i==0: i=1
        org=''.join(toks[:i]); nums=toks[i:]
        cut = clean_cut(nums[2]) if len(nums)>2 else ''
        yang=''
        if year==2023 and len(nums)>=5:      # 선발 합격 합격선 양성합격인원 양성합격선
            yang = clean_cut(nums[4])
        elif year==2025 and len(nums)>=4:     # 선발 합격 합격선 양성합격선
            yang = clean_cut(nums[3])
        passn = clean_cut(nums[1]) if len(nums)>1 else ''
        addcut(year, jl, tgt, org, cut, yang, passn)
    else:  # 2024: 직류급(대상) 기관 출원 응시 선발 필기합격 필기합격선(양성)
        pk = PACK2024.match(toks[0])
        if not pk:
            continue
        jl = pk.group(1); tgt = norm_target(pk.group(3)) if pk.group(3) else '일반'
        # 기관 then 5 nums
        rest = toks[1:]
        i=0
        while i<len(rest) and not ISNUM.match(rest[i]): i+=1
        if i==0: i=1
        org=''.join(rest[:i]); nums=rest[i:]
        if len(nums)<5: continue
        cutraw = nums[4]
        yang=''
        m=re.match(r'^(\d+)\((\d+)\)$', cutraw)
        if m:
            cut=m.group(1); yang=m.group(2)
        else:
            cut = clean_cut(cutraw)
        addcut(year, jl, tgt, org, cut, yang, clean_cut(nums[3]))

# ---------- 병합 & 요약 ----------
def compratio(app, sel):
    try:
        a=float(app); se=float(sel)
        if se>0: return f"{round(a/se,1)}:1"
    except: pass
    return ''

# 대상≠일반 fallback 인덱스: (year,jl,tgt) -> [keys]
from collections import defaultdict
CUTBY = defaultdict(list)
for k in CUT:
    CUTBY[(k[0],k[1],k[2])].append(k)

SRC = {2023:'2023년도 제3회 전라북도 지방공무원 공개경쟁임용 필기시험 응시현황.pdf',
       2024:'2024년도제3회전북특별자치도지방공무원임용필기시험응시현황.pdf',
       2025:'2025년도 제3회 전북특별자치도 지방공무원 임용시험 응시현황.pdf'}

rows=[]
matched=0; nocut=0; used=set()
for key, r in ATT.items():
    c = CUT.get(key); cut=yang=pass_=''; org=r['org']
    if c:
        cut, yang, pass_ = c; matched+=1; used.add(key)
    elif r['tgt']!='일반':
        cand=[k for k in CUTBY[(r['year'],r['jl'],r['tgt'])] if k not in used]
        if len(cand)==1:
            cut,yang,pass_=CUT[cand[0]]; matched+=1; used.add(cand[0])
            org='전북특별자치도'  # 구분모집은 도 일괄
        else:
            nocut+=1
    else:
        nocut+=1
    r2=dict(r); r2['org']=org
    comp_recv = compratio(r['app'], r['sel'])
    rows.append(r2 | dict(cut=cut, yang=yang, passn=pass_, comp_recv=comp_recv))

cut_only = [k for k in CUT if k not in ATT and k not in used]

from collections import Counter
yc = Counter(r['year'] for r in ATT.values())
print("응시현황 행수:", dict(yc), "총", len(ATT))
print("합격선 키수:", len(CUT))
print("병합 성공(합격선有):", matched, "/ 합격선無:", nocut)
print("합격선만 있고 응시현황 없음:", len(cut_only))
for k in cut_only[:40]:
    print("   CUT-ONLY", k, CUT[k])
print("--- 연도별 직류 ---")
for y in (2023,2024,2025):
    js = sorted(set(r['jl'] for r in ATT.values() if r['year']==y))
    print(y, len(js), js)
# 합격선 없는 응시현황 키 (미선발 후보) 일부
print("--- 합격선 없는 응시(상위40) ---")
nc=[k for k in ATT if k not in CUT]
for k in nc[:40]:
    print("   NOCUT", k, "memo=",ATT[k]['memo'])
print("총 NOCUT", len(nc))

# 스팟체크
def show(year, jl, tgt, org):
    for r in rows:
        if r['year']==year and r['jl']==jl and r['tgt']==tgt and nk(r['org'])==nk(org):
            print("  SPOT", year, jl, tgt, r['org'], "선발",r['sel'],"접수",r['app'],"응시",r['exam'],"율",r['rate'],"합격선",r['cut'],"양성",r['yang'])
print("--- 스팟체크 ---")
show(2023,'일반행정','일반','완주군')   # cut90 yang89
show(2024,'간호','일반','남원시')       # cut83 yang80
show(2025,'일반행정','일반','임실군')   # cut87 yang86
show(2023,'건축','장애인','전주시')     # fallback cut76
show(2025,'일반행정','장애인','전북특별자치도')  # cut53

HEADER=['지역','시험종류','연도','회차','시험구분','임용예정기관','직군','직렬','직류','직급','대상','선발예정인원','접수인원','경쟁률(접수/선발)','응시인원','응시율(%)','경쟁률(응시/선발)','필기합격인원','합격선','합격선기준','양성평등합격선','원본파일명','비고']
def csvrow(r):
    memo=r['memo']
    if r['cut']=='' and r['tgt']!='일반' and (r['exam'] in ('','-') or r['app'] in ('','-')):
        memo=(memo+' ' if memo else '')+''
    return ['전북','공무원',r['year'],r['hoe'],'공개경쟁',r['org'],'',r['jr'],r['jl'],r['gd'],r['tgt'],
            r['sel'],r['app'],r['comp_recv'],r['exam'],r['rate'],
            (r['comp']+':1' if r['comp'] and ':' not in str(r['comp']) else r['comp']),
            r.get('passn',''), r['cut'],'과목평균' if r['cut'] else '', r['yang'],
            SRC[r['year']], memo]

if '--write' in sys.argv:
    import io
    with open('검증_data.csv','a',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f)
        for r in sorted(rows,key=lambda x:(x['year'],x['jl'],x['tgt'])):
            w.writerow(csvrow(r))
    print("WROTE", len(rows),"rows")
