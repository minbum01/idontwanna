# -*- coding: utf-8 -*-
import csv, re, sys
import _kb_lib as L

D='C:/Users/admin/Documents/이민범 개발/합격선/합격선 최종모음/14 경북 공무원/'
ATT={2023:'2023년도 제1회 경상북도 지방공무원 9급 신규 임용 필기시험 응시 현황.pdf',
     2024:'2024년도 제1회 경상북도 지방공무원 공개경쟁임용시험 응시현황.pdf',
     2025:'2025년도 제1회 경상북도 지방공무원 공개경쟁임용시험 응시현황.pdf'}
CUT={2023:'(경상북도)2023년도 제1회 지방공무원 공개경쟁임용시험 합격선.pdf',
     2024:'2024년 경상북도 지방공무원시험 합격선.pdf',
     2025:'2025년 경상북도 지방공무원 공개경쟁임용시험 합격선.pdf'}

EXCL_JL={'시설관리','운전'}   # 경력경쟁
def is_excl(jl,tgt):
    return jl in EXCL_JL or tgt=='보훈청추천'

def gd_of(jl):
    return '8급' if jl in ('간호','보건진료') else '9급'

def ratio(a,b):
    try:
        a=int(a); b=int(b)
        if b>0: return f"{round(a/b,1)}:1"
    except: pass
    return ''

def cutval(s):
    s=(s or '').strip()
    if not s or s in ('-','비공개'): return s if s=='비공개' else ''
    m=re.match(r'^(\d+)(?:\.\d+)?$', s.replace(',',''))
    return m.group(1) if m else ''

rows_out=[]
report=[]
for y in (2023,2024,2025):
    cut,subs=L.parse_kb(D+CUT[y],'cut',want_sub=True)
    # 소계 자기검증
    assert all(int(ps)==tot for b,t,ps,tot in subs if ps.isdigit()), f'{y} 소계검증 실패'
    nexcl=0; nrow=0; norate=0
    for r in cut:
        jl,tgt,org=r['jikryu'],r['tgt'],r['org']
        if is_excl(jl,tgt):
            nexcl+=1; continue
        # 응시율 = 응시/접수 (합격선 문서 내부 일관)
        rate=''
        if r['app'].isdigit() and r['exam'].isdigit() and int(r['app'])>0:
            rate=str(round(int(r['exam'])/int(r['app'])*100,1))
        if not rate: norate+=1
        gd=gd_of(jl)
        jr=L.JR_OF.get(jl,jl)
        cv=cutval(r.get('cut',''))
        memo=''
        if not cv:
            if r['exam'].isdigit() and int(r['exam'])>0 and (not r['pass'] or r['pass']=='0'):
                memo='합격자없음'
            elif not r['exam'] or r['exam'] in ('-','0'):
                memo='응시자없음' if (r['app'] and r['app'] not in ('-','0')) else '미응시(출원없음)'
        rows_out.append(['경북','공무원',y,'1회','공개경쟁',org,'',jr,jl,gd,tgt,
            r['sel'],r['app'],ratio(r['app'],r['sel']),r['exam'],rate,ratio(r['exam'],r['sel']),
            r.get('pass',''),cv,'과목평균' if cv else '',
            '', CUT[y], memo])
        nrow+=1
    report.append((y,len(cut),nrow,nexcl,norate))

print("연도 | cut행 | 출력행 | 제외(경력) | 응시율없음")
for x in report: print(x)
print("총 출력행:",len(rows_out))
# 샘플
for r in rows_out[:3]+rows_out[-3:]:
    print(r)
# 8급 확인
print("8급 간호/보건진료 행수:",sum(1 for r in rows_out if r[9]=='8급'))

if '--write' in sys.argv:
    with open('검증_data.csv','a',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f)
        for r in rows_out: w.writerow(r)
    print("WROTE",len(rows_out))
