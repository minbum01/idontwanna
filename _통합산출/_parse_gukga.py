# -*- coding: utf-8 -*-
"""국가직 9급/7급 합격선 PDF -> 검증_data.csv 형식 행 생성.
extract_tables()로 셀 단위 추출(양성 스택 분리 확실). 결과는 국가직_rows.csv + 검증 합계 출력."""
import pdfplumber, os, csv, re, io

D = r"C:\Users\user\OneDrive\Desktop\합격선\idontwanna\합격선 최종모음\국가직"
OUTDIR = os.path.dirname(__file__)

COLS = ['지역','시험종류','연도','회차','시험구분','임용예정기관','직군','직렬','직류','직급','대상',
        '선발예정인원','접수인원','경쟁률(접수/선발)','응시인원','응시율(%)','경쟁률(응시/선발)',
        '필기합격인원','합격선','합격선기준','양성평등합격선','원본파일명','비고']

HAENG = {'행정','직업상담','세무','관세','통계','감사','교정','보호','검찰','마약수사','출입국관리','철도경찰','외무영사'}
GISUL = {'공업','농업','임업','시설','방재안전','전산','방송통신','환경'}

def jikgun(jikryeol):
    if jikryeol in HAENG: return '행정직군'
    if jikryeol in GISUL: return '기술직군'
    return ''

def n(s):
    """숫자 문자열 정리: 콤마 제거, '-'/빈칸 -> ''"""
    if s is None: return ''
    s = str(s).strip().replace(',', '')
    if s in ('-', ''): return ''
    return s

def num(s):
    s = n(s)
    try: return float(s)
    except: return None

def fmt_rate(a, b):
    """a/b 비율 -> 'X.X:1'"""
    if a is None or b is None or b == 0: return ''
    return f"{a/b:.1f}:1"

def fmt_yul(eung, jeop):
    if eung is None or jeop is None or jeop == 0: return ''
    return f"{eung/jeop*100:.1f}"

# 모집단위 파싱: 직렬(직류[:대상])  /  괄호없으면 권역명
def parse_unit(name):
    name = name.strip()
    m = re.match(r'^(.+?)\((.+)\)$', name)
    if not m:
        return None  # 권역(괄호 없음)
    jik = m.group(1).strip()
    inner = m.group(2).strip()
    if ':' in inner:
        jr, dae = inner.rsplit(':', 1)
        jr, dae = jr.strip(), dae.strip()
    else:
        jr, dae = inner, '일반'
    dae_map = {'저소득':'저소득층'}
    dae = dae_map.get(dae, dae)
    return jik, jr, dae

SKIP_C0 = {'모 집 단 위', '전 모집단위 합계', '일반 모집 계', '장애인 모집 계', '저소득 모집 계', '저소득층 모집 계'}

def is_haps_table(t):
    """합격선 표만(7컬럼, 헤더 col4에 '합격선'). 점수분포/성별/연령표 제외."""
    if not t: return False
    if max(len(r) for r in t) != 7: return False
    for r in t[:2]:
        if len(r) >= 5 and r[4] and '합격선' in str(r[4]):
            return True
    return False

def is_data_row(row):
    if not row or len(row) < 6: return False
    c0 = (row[0] or '').strip()
    if not c0 or c0 in SKIP_C0: return False
    if '합격선' in c0 or '모 집' in c0: return False
    if num(row[1]) is None: return False  # 선발예정인원이 숫자여야 데이터행
    return True

def parse_haps_9(cell):
    """9급 합격선 셀 -> (합격선, 양성, 비고). col4."""
    if cell is None: return '', '', ''
    lines = [l.strip() for l in str(cell).split('\n') if l.strip()]
    if not lines: return '', '', ''
    main = lines[0]
    yang = ''
    bigo = ''
    if num(main) is None:  # '전원과락','미응시' 등 텍스트
        return '', '', main
    # 둘째 줄: 양성 (형식: '82.00(양성)' 또는 '(81.00)')
    if len(lines) > 1:
        mm = re.search(r'(\d+\.?\d*)', lines[1])
        if mm: yang = mm.group(1)
    return main, yang, bigo

def parse_haps_7(cell):
    """7급 합격선 셀 -> (합격선, 양성, 비고). 'main\n(지방/양성)'."""
    if cell is None: return '', '', ''
    lines = [l.strip() for l in str(cell).split('\n') if l.strip()]
    if not lines: return '', '', ''
    main = lines[0]
    yang = ''; bigo = ''
    if num(main) is None:
        # 7급은 합격선이 '-'이면 사유가 별도 비고열(col6)에 있음 -> '-'는 비고에 넣지 않음
        return '', '', ('' if main == '-' else main)
    if len(lines) > 1:
        mm = re.match(r'\(([^/]*)/([^)]*)\)', lines[1])
        if mm:
            jibang = mm.group(1).strip()
            yangs = mm.group(2).strip()
            if num(yangs) is not None: yang = yangs
            if num(jibang) is not None: bigo = f"지방인재{jibang}"
    return main, yang, bigo

def haps_count(cell):
    """합격인원 셀 첫 줄(메인)."""
    if cell is None: return ''
    lines = [l.strip() for l in str(cell).split('\n') if l.strip()]
    return n(lines[0]) if lines else ''

def process_9(fn, year):
    rows = []
    parent = None  # 지역구분모집 부모 (직렬,직류,대상)
    with pdfplumber.open(os.path.join(D, fn)) as pdf:
        for page in pdf.pages:
            for t in page.extract_tables():
                if not is_haps_table(t): continue
                for r in t:
                    if not is_data_row(r): continue
                    name = r[0].strip()
                    seonbal, chulwon, eungsi = n(r[1]), n(r[2]), n(r[3])
                    haps, yang, bigo = parse_haps_9(r[4])
                    fcount = haps_count(r[5])
                    pu = parse_unit(name)
                    if pu:
                        jik, jr, dae = pu
                        if haps == '' and (r[4] is None or str(r[4]).strip() == '-'):
                            # 지역구분 부모행(합격선 '-') -> 데이터행 아님, 부모로 등록
                            parent = (jik, jr, dae)
                            continue
                        parent = None
                        gigwan = ''
                    else:
                        # 권역 sub-row
                        if not parent:  # 안전장치
                            continue
                        jik, jr, dae = parent
                        gigwan = name  # 권역 = 임용예정기관
                    rows.append(mkrow('국가직','공무원',year,'',gigwan,jik,jr,dae,'9급',
                                      seonbal,chulwon,eungsi,fcount,haps,yang,bigo,fn))
    return rows

def process_7(fn, year, hoecha):
    rows = []
    with pdfplumber.open(os.path.join(D, fn)) as pdf:
        for page in pdf.pages:
            for t in page.extract_tables():
                if not is_haps_table(t): continue
                for r in t:
                    if not is_data_row(r): continue
                    if len(r) < 6: continue
                    name = r[0].strip()
                    pu = parse_unit(name)
                    if not pu:  # 7급은 전부 전국, 괄호 없는 행은 점수분포표 등 -> 스킵
                        continue
                    jik, jr, dae = pu
                    seonbal, chulwon, eungsi = n(r[1]), n(r[2]), n(r[3])
                    haps, yang, bigo = parse_haps_7(r[4])
                    fcount = haps_count(r[5])
                    # 비고열(col6) 텍스트(응시자없음/전원과락) 병합
                    extra = (r[6] or '').strip() if len(r) > 6 else ''
                    if extra and extra not in ('-',''):
                        bigo = (bigo + ' ' + extra).strip() if bigo else extra
                    rows.append(mkrow('국가직','공무원',year,hoecha,'',jik,jr,dae,'7급',
                                      seonbal,chulwon,eungsi,fcount,haps,yang,bigo,fn))
    return rows

def mkrow(region, jong, year, hoecha, gigwan, jik, jr, dae, geup,
          seonbal, chulwon, eungsi, fcount, haps, yang, bigo, fn):
    sb, cw, eu = num(seonbal), num(chulwon), num(eungsi)
    d = {c:'' for c in COLS}
    d['지역']=region; d['시험종류']=jong; d['연도']=str(year); d['회차']=hoecha
    d['시험구분']='공개경쟁'; d['임용예정기관']=gigwan; d['직군']=jikgun(jik)
    d['직렬']=jik; d['직류']=jr; d['직급']=geup; d['대상']=dae
    d['선발예정인원']=seonbal; d['접수인원']=chulwon
    d['경쟁률(접수/선발)']=fmt_rate(cw, sb)
    d['응시인원']=eungsi; d['응시율(%)']=fmt_yul(eu, cw)
    d['경쟁률(응시/선발)']=fmt_rate(eu, sb)
    d['필기합격인원']=fcount; d['합격선']=haps
    d['합격선기준']='과목평균' if haps else ''
    d['양성평등합격선']=yang; d['원본파일명']=fn; d['비고']=bigo
    return d

JOBS = [
 (process_9, "2023년도 국가공무원 9급 공개경쟁채용 필기시험 합격선 (1).pdf", 2023),
 (process_9, "2024년도 국가공무원 9급 공개경쟁채용 필기시험 합격선 (1).pdf", 2024),
 (process_9, "2025년도 국가공무원 9급 공개경쟁채용 필기시험 합격선 (2).pdf", 2025),
 (process_9, "★2026년도 국가공무원 9급 공개경쟁채용 필기시험 합격선[배포용문서] (1).pdf", 2026),
]
JOBS7 = [
 ("(붙임) 2023년도 국가직 7급 공채 제1차시험 합격선 및 합격자 통계 (1).pdf", 2023, "1차-PSAT"),
 ("(붙임) 2023년도 국가공무원 7급 공개경쟁채용 제2차시험 합격선 및 합격자 통계 .pdf", 2023, "2차-전공"),
 ("2024년도 국가공무원 7급 공개경쟁채용 제1차시험 합격선 및 합격자 통계 (1).pdf", 2024, "1차-PSAT"),
 ("(붙임) 2024년도 국가직 7급 공채 제2차시험 합격선 및 합격자 통계 (1).pdf", 2024, "2차-전공"),
 ("2025년도 국가직 7급 공개경쟁채용 제1차시험 합격선 및 합격자 통계(수정) (1).pdf", 2025, "1차-PSAT"),
 ("2025년도 국가직 7급 공개경쟁채용 제2차시험 합격선 및 합격자 통계 (1).pdf", 2025, "2차-전공"),
]

all_rows = []
log = io.StringIO()
for fnc, fn, yr in JOBS:
    rs = fnc(fn, yr)
    all_rows += rs
    tot_sb = sum(num(r['선발예정인원']) or 0 for r in rs)
    tot_cw = sum(num(r['접수인원']) or 0 for r in rs)
    log.write(f"[9급 {yr}] rows={len(rs)} 선발합={int(tot_sb)} 접수합={int(tot_cw)}\n")
for fn, yr, hc in JOBS7:
    rs = process_7(fn, yr, hc)
    all_rows += rs
    tot_sb = sum(num(r['선발예정인원']) or 0 for r in rs)
    tot_cw = sum(num(r['접수인원']) or 0 for r in rs)
    log.write(f"[7급 {yr} {hc}] rows={len(rs)} 선발합={int(tot_sb)} 접수합={int(tot_cw)}\n")

with open(os.path.join(OUTDIR, "국가직_rows.csv"), "w", encoding="utf-8-sig", newline='') as fp:
    w = csv.DictWriter(fp, fieldnames=COLS)
    w.writeheader()
    w.writerows(all_rows)

log.write(f"\n총 {len(all_rows)}행\n")
with open(os.path.join(OUTDIR, "_tmp_parse_log.txt"), "w", encoding="utf-8") as fp:
    fp.write(log.getvalue())
print(log.getvalue())
