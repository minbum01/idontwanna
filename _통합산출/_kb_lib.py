# -*- coding: utf-8 -*-
import pdfplumber, re

TARGETS = ('일반','장애인','저소득','저소득층','보훈청추천','보훈부추천','보훈')
def clean(x):
    x = re.sub(r'\s+','', x or '')
    for t in ('직렬(직류)','직렬(직','(직류)','류)'):
        x = x.replace(t,'')
    return x

def split_label(lab):
    """ '일반행정(일반)' -> (직류=일반행정, 대상=일반) ; '전산' -> (전산, 일반) """
    m = re.match(r'^(.+?)\(([가-힣]+)\)$', lab)
    if m and m.group(2) in TARGETS:
        jr, tg = m.group(1), m.group(2)
    else:
        jr, tg = lab, '일반'
    if tg in ('저소득','저소득층'): tg='저소득층'
    if tg in ('보훈청추천','보훈부추천','보훈'): tg='보훈청추천'
    return jr, tg

JR_OF = {  # 직류 -> 직렬
 '일반행정':'행정','지방세':'세무','세무':'세무','전산':'전산','사회복지':'사회복지','사서':'사서','속기':'속기',
 '방호':'방호','일반기계':'공업','농업기계':'공업','일반전기':'공업','일반화공':'공업','원자력':'공업',
 '일반농업':'농업','축산':'농업','산림자원':'녹지','산림보호':'녹지','조경':'녹지',
 '일반해양':'해양수산','일반수산':'해양수산','선박항해':'해양수산','선박기관':'해양수산',
 '보건':'보건','일반환경':'환경','도시계획':'환경','일반토목':'시설','건축':'시설','지적':'시설','교통시설':'시설',
 '방재안전':'방재안전','통신기술':'방송통신','시설관리':'시설관리','운전':'운전','간호':'간호','보건진료':'보건진료',
 '식품위생':'식품위생','기록관리':'기록연구','조리':'조리','약무':'약무','의료기술':'의료기술','임상심리':'임상심리',
}
def _num(x):
    x=(x or '').strip().replace(',','')
    if x in ('-','',None): return ''
    return re.sub(r'\s+','',x)  # join split digits '3 3'->'33'

def _lab_parse(lab):
    """ -> (base or '', 대상 or None). bare base는 대상 None(미명시) → 괄호대상 우선."""
    lab=lab.strip()
    if not lab or lab in ('직렬(직류)','직류','계급','직렬'): return '',None
    m=re.match(r'^(.*?)\(([가-힣]+)\)$', lab)
    if m and m.group(2) in TARGETS:
        tg=m.group(2)
        tg='저소득층' if tg in ('저소득','저소득층') else ('보훈청추천' if tg in ('보훈청추천','보훈부추천','보훈') else tg)
        return m.group(1), tg
    if not lab.startswith('('):
        return lab, None
    return '', None

def parse_kb(path, kind, want_sub=False):
    """소계=그룹경계. 라벨은 col2만 first-found, base는 그룹간 carry, tgt는 그룹별.
    각 그룹 앞의 소계 숫자를 그룹에 부착(검증용)."""
    out=[]; subs=[]
    flat=[]
    with pdfplumber.open(path) as pdf:
        for pg in pdf.pages:
            for tb in pg.extract_tables():
                for row in tb:
                    if len(row)>=9: flat.append(row)
    last_base=''
    buf=[]; buf_base=''; buf_tgt=''; pend_sub=None
    def flush():
        nonlocal last_base
        if not buf:
            return
        base = buf_base or last_base
        tgt = buf_tgt or '일반'
        if base: last_base=base
        jr=JR_OF.get(base,base)
        gd='8급' if base in ('간호','보건진료') else '9급'
        tot=sum(int(_num(r[4])) for r in buf if _num(r[4]).isdigit())
        for r in buf:
            org=clean(r[3])
            d=dict(gd=gd,jr=jr,jikryu=base,tgt=tgt,org=org,
                   sel=_num(r[4]),app=_num(r[5]),exam=_num(r[6]))
            if kind=='att': d['rate']=(r[7] or '').strip(); d['memo']=(r[8] or '').strip()
            else: d['pass']=_num(r[7]); d['cut']=(r[8] or '').strip()
            out.append(d)
        if pend_sub is not None:
            subs.append((base,tgt,pend_sub,tot))
    for row in flat:
        c2=clean(row[2]); org=clean(row[3])
        b,t=_lab_parse(c2)
        if org=='소계':
            flush()
            buf=[]; buf_base=''; buf_tgt=''
            pend_sub=_num(row[4])
            if b: buf_base=b
            if t: buf_tgt=t
            continue
        if org in ('합계','임용예정기관','계급','직렬(직류)','') or org is None:
            continue
        if not re.search(r'[가-힣]',org):
            continue
        if b and not buf_base: buf_base=b
        if t and not buf_tgt: buf_tgt=t
        buf.append(row)
    flush()
    return (out,subs) if want_sub else out

if __name__=='__main__':
    import sys
    rs=parse_kb(sys.argv[1],'att' if len(sys.argv)<3 else sys.argv[2])
    print('rows',len(rs))
    from collections import Counter
    cnt=Counter((r['gd'],r['jr'],r['jikryu'],r['tgt']) for r in rs)
    for k in cnt: print('  ',k,'x',cnt[k])
    print('선발합',sum(int(r['sel']) for r in rs if r['sel'].isdigit()))
