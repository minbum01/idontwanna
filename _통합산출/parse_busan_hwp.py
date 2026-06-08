# -*- coding: utf-8 -*-
"""부산 공무원 HWP/hwpx(배포용)의 PrvText에서 합격선 표 -> 통일 양식. 원본 읽기전용."""
import olefile, re, os, glob, csv

ROOT = r"C:/Users/admin/Documents/이민범 개발/합격선/합격선 최종모음"
HEADERS = ["지역","시험종류","연도","회차","시험구분","임용예정기관","직군","직렬","직류","직급","대상",
           "선발예정인원","접수인원","접수여성","경쟁률(접수/선발)","응시인원","응시여성","응시율","경쟁률(응시/선발)",
           "필기합격인원","필기합격여성","합격선","양성평등성별","양성평등합격선","최종합격인원","최종합격여성",
           "원본파일명","비고"]

GUBUN = {"공개경쟁":"공개경쟁","경력경쟁":"경력경쟁","공개경쟁임용":"공개경쟁","경력경쟁임용":"경력경쟁"}
JIKGUP_RE = re.compile(r'^(\d+급|연구사|지도사|연구관)$')

def prvtext(path):
    o=olefile.OleFileIO(path)
    d=o.openstream('PrvText').read().decode('utf-16-le','ignore')
    o.close()
    return d

def num(t):
    t=t.replace(',','').replace(' ','').strip()
    if t in ('','-','–'): return ''
    return t

def parse_name(tok):
    name=re.sub(r'-+',' ',tok).strip()
    m=re.match(r'^(.+?)\((.+?)\)\s*(.*)$', name)
    if not m: return None
    jikryeol=m.group(1).strip()
    jikryu=m.group(2).strip()
    rest=m.group(3).strip()
    if jikryeol.endswith('직') and len(jikryeol)>1: jikryeol=jikryeol[:-1]
    daesang='일반'
    if '장애' in rest: daesang='장애인'
    elif '저소득' in rest: daesang='저소득층'
    elif rest: daesang=rest.lstrip('_')
    return jikryeol,jikryu,daesang

def parse_file(path, region, kind, yr, rd):
    txt=prvtext(path)
    toks=re.findall(r'<(.*?)>', txt, flags=re.S)
    rows=[]
    cur_gubun=cur_jikgun=cur_jikgup=''
    i=0; n=len(toks)
    started=False
    while i<n:
        t=toks[i].strip(); norm=t.replace(' ','')
        # 헤더행 시작 표식 이후부터
        if norm=='구분':
            started=True; i+=1; continue
        if not started: i+=1; continue
        if norm.startswith('소계') or '개직렬' in norm or '개직류' in norm:
            # 소계 행: 값 토큰들 건너뛰기
            i+=1
            while i<n and '(' not in toks[i] and toks[i].replace(' ','') not in GUBUN and not toks[i].strip().replace(' ','').endswith('직군'):
                i+=1
            continue
        if norm in GUBUN:
            cur_gubun=GUBUN[norm]; i+=1; continue
        if norm.endswith('직군') or norm in ('연구직','전문경력관'):
            cur_jikgun=norm; i+=1; continue
        if '(' in t:
            if not cur_gubun:  # 헤더/소계 전 토큰 무시
                i+=1; continue
            pn=parse_name(t)
            if not pn: i+=1; continue
            jikryeol,jikryu,daesang=pn
            i+=1
            # 직급?
            if i<n and JIKGUP_RE.match(toks[i].strip()):
                cur_jikgup=toks[i].strip(); i+=1
            vals=[]
            while i<n and len(vals)<5:
                vals.append(toks[i]); i+=1
            # 비고(빈칸) 소비
            if i<n and toks[i].strip()=='': i+=1
            vals=(vals+['']*5)[:5]
            sel,chul,eung,hap,cut=[num(v) for v in vals]
            rows.append([region,kind,yr,rd,cur_gubun,'',cur_jikgun,jikryeol,jikryu,cur_jikgup,daesang,
                         sel,chul,'','',eung,'','','',hap,'',cut,'','','','',os.path.basename(path),''])
            continue
        i+=1
    return rows

def meta(folder, fn):
    name=re.sub(r'^\d+\s*','',folder).strip(); parts=name.split()
    region=parts[0]; kind=' '.join(parts[1:]) if len(parts)>1 else ''
    yr=re.search(r'(\d{4})',fn); rd=re.search(r'제\s*(\d+)\s*회',fn)
    return region,kind,(yr.group(1) if yr else ''),(rd.group(1)+'회' if rd else '')

if __name__=='__main__':
    out=[]
    for f in glob.glob(os.path.join(ROOT,'*','*.hwp'))+glob.glob(os.path.join(ROOT,'*','*.hwpx')):
        folder=os.path.basename(os.path.dirname(f)); fn=os.path.basename(f)
        if '부산' not in folder or '공무원' not in folder: continue
        region,kind,yr,rd=meta(folder,fn)
        try:
            r=parse_file(f,region,kind,yr,rd)
            print(f"{fn} -> {len(r)} rows")
            out+=r
        except Exception as e:
            print(f"{fn} ERR {e}")
    OUT=os.path.join(os.path.dirname(__file__),'부산_공무원_hwp.csv')
    with open(OUT,'w',encoding='utf-8-sig',newline='') as fp:
        w=csv.writer(fp); w.writerow(HEADERS); w.writerows(out)
    print('TOTAL', len(out), '->', OUT)
    print('--- sample ---')
    for r in out[:8]: print(r[:12]+[r[21]])
