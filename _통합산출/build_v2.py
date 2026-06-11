# -*- coding: utf-8 -*-
"""검증_data.csv(사용자 확인 완료분만) -> 합격선_관리_v2.html (깔끔·라이트). 파일 하나씩 확인하며 누적."""
import csv, json, os
D=os.path.dirname(__file__)
SRC=os.path.join(D,"검증_data.csv")
OUT=os.path.join(D,"합격선_관리_v2.html")
TOTAL_FILES=250  # 대략(34개 폴더 × ~7)

import glob as _glob
# 원본 파일 폴더(하이퍼링크용). 다른 PC 이식성: 기본은 이 폴더의 상위에 있는 "합격선 최종모음".
# 환경변수 HAPGYEOK_SRC 로 덮어쓸 수 있음.
BASE=os.environ.get("HAPGYEOK_SRC") or os.path.normpath(os.path.join(D,"..","합격선 최종모음")).replace("\\","/")
_paths={}
for _f in _glob.glob(BASE+"/**/*",recursive=True):
    if os.path.isfile(_f):
        _paths[os.path.basename(_f)]="file:///"+_f.replace("\\","/").replace(" ","%20")
with open(SRC,encoding="utf-8-sig") as fp:
    rows=list(csv.DictReader(fp))
data=json.dumps(rows,ensure_ascii=False)
done_files=sorted(set(r["원본파일명"] for r in rows if r["원본파일명"]))
file_links=json.dumps(_paths,ensure_ascii=False)

# ===== 미완·확인필요 이슈 (자동 탐지 + 수기 병합) =====
from collections import defaultdict as _dd
ALL_REG=['서울','부산','대구','인천','광주','대전','울산','경기','강원','충북','충남','전북','전남','경북','경남','제주','세종']
USER_PREP={'강원','충북','충남','전북','전남','경북'}  # 사용자가 엑셀로 준비중
_done=set((r['지역'],r['시험종류']) for r in rows)
issues=[]
for _reg in ALL_REG:
    if _reg in USER_PREP: continue
    for _jt in ['공무원','교행']:
        if (_reg,_jt) not in _done:
            issues.append({'구분':'미입력','지역':_reg,'항목':_jt+' 합격선','상태':'❌ 미처리','메모':'원본 폴더에 파일 있음 · 합격선 아직 입력 안 함'})
def _misun(r):  # 미선발/비공개 → 접수·응시 0 이 정상(이슈 아님)
    return ('미선발' in r['비고']) or ('비공개' in r['비고']) or (not r['합격선'].strip() and r['필기합격인원'].strip() in ('','0'))
_REASON={
 ('광주','공무원'): '【원본 일부 부재 — 제2회 경채·고졸분】 광주 공무원은 제1회(공개경쟁)와 제2회(경력경쟁·고졸 등)로 나뉘는데, 우리가 가진 응시(출원)현황은 제1회 공채분뿐입니다. 아래 7행은 모두 제2회에서 뽑는 전형이라 출원(접수)인원 자료가 없습니다.\\n▸ 의료기술 경력경쟁 4행: 2024년 방사선·임상병리, 2025년 임상병리·물리치료\\n▸ 공업(일반전기) 기술계고졸 3행: 2023·2024·2025년\\n이 7행은 합격선·필기합격인원·응시인원은 모두 채워져 있고 출원(접수)인원만 비어, 경쟁률(접수/선발)과 응시율만 산출하지 못합니다.\\n→ 필요한 자료: 광주광역시 제2회 임용시험 원서접수(출원)현황(2023~2025).',
 ('부산','공무원'): '【원본 부재 — 1건】 2025년 제2회 행정(일반행정) 일반 1행만 접수(출원)인원이 비어있습니다. 그 제2회 합격선 파일의 양식이 "선발/응시/필기합격/합격선"으로, 출원(접수) 칸이 아예 없습니다(이 행은 선발 10·응시 564·합격선 87은 있음). 부산 공무원 폴더에 2023~2025 응시/출원 현황 파일이 따로 없고, 합격선 파일 자체에서 출원을 가져오는데 제2회 파일엔 그 칸이 없어 못 채움. → 원본에 출원자료가 없어 보완 불가(1행만 미상으로 남김).',
}
_er=_dd(lambda:{'접수':[],'응시':[]})
for r in rows:
    if _misun(r): continue
    _lab=f"{r['연도']} {r['직렬']}"+(f"·{r['직류']}" if r['직류'] and r['직류']!=r['직렬'] else '')+(f"({r['대상']})" if r['대상'] not in ('일반','') else '')+(f" [{r['임용예정기관']}]" if r['임용예정기관'] else '')
    if not r['접수인원'].strip(): _er[(r['지역'],r['시험종류'])]['접수'].append(_lab)
    if not r['응시인원'].strip(): _er[(r['지역'],r['시험종류'])]['응시'].append(_lab)
for (_reg,_jt),_e in sorted(_er.items()):
    _rsn=_REASON.get((_reg,_jt),'사유 확인 필요(데이터는 있을 수 있으니 수기 점검).')
    for _fld in ['접수','응시']:
        if _e[_fld]:
            _it=_e[_fld]; _show=', '.join(_it[:24])+(f' …외 {len(_it)-24}건' if len(_it)>24 else '')
            issues.append({'구분':f'{_fld}인원 미반영','지역':_reg,'항목':f'{_jt} · {_fld}인원 {len(_it)}건','상태':'△ 보완대상','메모':_rsn+'  ▷ 해당 행: '+_show})
_man=os.path.join(D,'이슈_수기.csv')
if os.path.exists(_man):
    with open(_man,encoding='utf-8-sig') as fp:
        for r in csv.DictReader(fp):
            issues.append({'구분':r['구분'],'지역':r['지역'],'항목':r['항목'],'상태':r['상태'],'메모':r.get('사유/메모','')})
issues_json=json.dumps(issues,ensure_ascii=False)

HTML=r"""<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>합격선 관리 v2 (검증본)</title>
<style>
:root{--bg:#f6f8fb;--card:#fff;--line:#e6e9ef;--txt:#1f2937;--mut:#6b7280;--acc:#2563eb;--cut:#b45309;--ok:#16a34a}
*{box-sizing:border-box}body{margin:0;font-family:'Pretendard','Malgun Gothic',sans-serif;background:var(--bg);color:var(--txt);font-size:13px}
header{padding:14px 22px;background:#fff;border-bottom:1px solid var(--line)}
h1{margin:0;font-size:17px}.sub{color:var(--mut);font-size:12px;margin-top:3px}
.bar{height:8px;background:#eceff3;border-radius:8px;overflow:hidden;margin-top:8px;max-width:520px}
.bar>i{display:block;height:100%;background:linear-gradient(90deg,#22c55e,#16a34a)}
.wrap{padding:18px 22px;max-width:1400px}
.cards{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:14px}
.kpi{background:#fff;border:1px solid var(--line);border-radius:10px;padding:11px 15px;min-width:96px}
.kpi .n{font-size:20px;font-weight:700;color:var(--acc)}.kpi .l{color:var(--mut);font-size:11px}
.filters{display:flex;gap:8px;flex-wrap:wrap;align-items:flex-end;margin-bottom:12px}
.fl{display:flex;flex-direction:column;gap:3px}.fl label{font-size:10px;color:var(--mut)}
select,input{background:#fff;border:1px solid var(--line);border-radius:7px;padding:6px 9px;font-size:13px}
select:focus,input:focus{outline:none;border-color:var(--acc)}
.count{color:var(--mut);margin-left:auto;align-self:center}
.tblwrap{overflow:auto;max-height:74vh;border:1px solid var(--line);border-radius:10px;background:#fff}
table{border-collapse:collapse;width:100%;table-layout:fixed}
th,td{padding:6px 9px;border-bottom:1px solid #f1f3f5;text-align:left;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
thead th{position:sticky;top:0;background:#f8fafc;font-size:12px;font-weight:600;border-bottom:1.5px solid var(--line)}
tbody tr:hover{background:#f8fbff}.r{text-align:right}
.tag{padding:1px 7px;border-radius:10px;font-size:11px;font-weight:600}
.t-공무원{background:#dbeafe;color:#1e40af}.t-교행{background:#f3e8ff;color:#6b21a8}
.cut{font-weight:700;color:var(--cut);text-align:right}
.empty{padding:50px;text-align:center;color:var(--mut)}
.done{color:var(--ok);font-weight:600}
.tabs{display:flex;gap:4px;padding:0 22px;background:#fff;border-bottom:1px solid var(--line)}
.tab{padding:10px 16px;border:none;background:none;font-size:13px;font-weight:600;color:var(--mut);cursor:pointer;border-bottom:2px solid transparent}
.tab.on{color:var(--acc);border-bottom-color:var(--acc)}
.tab .badge{background:#fee2e2;color:#b91c1c;border-radius:9px;padding:0 6px;font-size:11px;margin-left:5px}
.igrp{margin:14px 0 4px;font-weight:700;font-size:13px;color:var(--txt)}
.itbl{width:100%;border-collapse:collapse;background:#fff;border:1px solid var(--line);border-radius:10px;overflow:hidden}
.itbl th,.itbl td{padding:8px 11px;border-bottom:1px solid #f1f3f5;text-align:left;font-size:13px}
.itbl th{background:#f8fafc;font-size:12px;color:var(--mut)}
.st-미입력,.st-x{color:#b91c1c;font-weight:600}
.icard{border:1px solid var(--line);border-left:4px solid var(--acc);border-radius:8px;padding:11px 14px;margin-bottom:9px;background:#fff}
.icard.prep{border-left-color:#a855f7}.icard.gap{border-left-color:#f59e0b}
.ihead{display:flex;gap:9px;align-items:center;flex-wrap:wrap;margin-bottom:6px}
.ireg{font-weight:700;font-size:14px}
.ibadge2{font-size:11px;background:#eef2ff;color:var(--acc);border-radius:10px;padding:1px 9px;font-weight:600}
.istat{font-size:12px;color:var(--cut);font-weight:600}
.imemo{font-size:13px;line-height:1.75;color:#374151;white-space:pre-wrap;word-break:break-word}
.imemo .rows{display:block;margin-top:6px;padding:7px 10px;background:#f8fafc;border-radius:6px;font-size:12px;color:#6b7280}
</style></head><body>
<header><h1>✅ 합격선 관리 v2 — 검증본</h1>
<div class="sub" id="meta"></div>
<div class="bar"><i id="prog"></i></div>
</header>
<div class="tabs">
<button class="tab on" data-t="data" onclick="tab('data')">📋 검증 데이터</button>
<button class="tab" data-t="issue" onclick="tab('issue')">⚠️ 미완·확인필요 <span class="badge" id="ibadge"></span></button>
</div>
<div class="wrap" id="tab-data">
<div class="cards" id="cards"></div>
<div class="filters" id="filters"></div>
<div id="tbl"></div>
</div>
<div class="wrap" id="tab-issue" style="display:none"><div id="issues"></div></div>
<script>
const DB=__DATA__, DONE=__DONE__, TOTAL=__TOTAL__, LINKS=__LINKS__, ISSUES=__ISSUES__;
const $=s=>document.querySelector(s),el=(t,c,h)=>{const e=document.createElement(t);if(c)e.className=c;if(h!=null)e.innerHTML=h;return e};
const uniq=(a,k)=>[...new Set(a.map(r=>r[k]).filter(Boolean))].sort((x,y)=>String(x).localeCompare(y,'ko'));
const COLS=[['지역'],['시험종류','t'],['연도'],['회차'],['시험구분'],['임용예정기관'],['직군'],['직렬'],['직류'],['직급'],['대상'],
 ['선발예정인원','선발','r'],['접수인원','접수','r'],['경쟁률(접수/선발)','경쟁률↓','r'],
 ['응시인원','응시','r'],['응시율(%)','응시율','r'],['경쟁률(응시/선발)','응시경쟁률','r'],
 ['필기합격인원','필기합격','r'],['합격선','합격선','cut'],['합격선기준','기준'],['양성평등합격선','양성','r'],
 ['원본파일명','출처'],['비고']];
const W={'지역':54,'시험종류':62,'연도':52,'회차':48,'시험구분':76,'임용예정기관':110,'직군':82,'직렬':82,'직류':100,'직급':52,'대상':78,
 '선발예정인원':50,'접수인원':58,'경쟁률(접수/선발)':78,'응시인원':56,'응시율(%)':60,'경쟁률(응시/선발)':80,
 '필기합격인원':60,'합격선':68,'합격선기준':72,'양성평등합격선':58,'원본파일명':240,'비고':120};
$('#meta').innerHTML=`확인 완료 <b class="done">${DONE.length}</b> / 약 ${TOTAL} 파일 · 검증 행 <b>${DB.length.toLocaleString()}</b>`;
$('#prog').style.width=Math.min(100,DONE.length/TOTAL*100)+'%';
const regs=uniq(DB,'지역');
[['확인 파일',DONE.length],['검증 행',DB.length],['지역',regs.length],['공무원',DB.filter(r=>r['시험종류']=='공무원').length],['교행',DB.filter(r=>r['시험종류']=='교행').length]].forEach(([l,n])=>$('#cards').appendChild(el('div','kpi',`<div class="n">${n}</div><div class="l">${l}</div>`)));
const F=['지역','시험종류','연도','임용예정기관','직급','직렬','직류','대상'];
F.forEach(k=>{const w=el('div','fl');w.innerHTML=`<label>${k}</label>`;const s=el('select');s.id='f-'+k;s.innerHTML='<option value="">전체</option>'+uniq(DB,k).map(x=>`<option ${k=='직급'&&x=='9급'?'selected':''}>${x}</option>`).join('');s.onchange=draw;w.appendChild(s);$('#filters').appendChild(w)});
const qw=el('div','fl');qw.innerHTML='<label>검색</label>';const q=el('input');q.id='f-q';q.placeholder='직류·파일명…';q.oninput=draw;qw.appendChild(q);$('#filters').appendChild(qw);
const cnt=el('span','count');cnt.id='cnt';$('#filters').appendChild(cnt);
function draw(){
 let rows=DB.slice();
 F.forEach(k=>{const v=$('#f-'+k).value;if(v)rows=rows.filter(r=>r[k]==v)});
 const s=$('#f-q').value.trim();if(s)rows=rows.filter(r=>Object.values(r).some(v=>String(v).includes(s)));
 $('#cnt').textContent=rows.length.toLocaleString()+'행';
 if(!DB.length){$('#tbl').innerHTML='<div class="empty">아직 확인된 파일이 없습니다.<br>파일을 하나씩 확인하면 여기에 쌓입니다.</div>';return}
 const tw=COLS.reduce((a,[k])=>a+(W[k]||80),0);
 let h=`<div class="tblwrap"><table style="min-width:${tw}px"><colgroup>`+COLS.map(([k])=>`<col style="width:${W[k]||80}px">`).join('')+'</colgroup><thead><tr>'+COLS.map(([k,t])=>`<th>${t||k}</th>`).join('')+'</tr></thead><tbody>';
 h+=rows.map(r=>'<tr>'+COLS.map(([k,t,c])=>{let v=r[k]==null?'':r[k];
   if(c=='t')return `<td><span class="tag t-${v}">${v}</span></td>`;
   if(c=='cut')return `<td class="cut" title="${v}">${v}</td>`;
   if(k=='원본파일명'){const href=LINKS[v];return href?`<td><a href="${href}" target="_blank" title="${v}" style="color:var(--acc);text-decoration:none">${v.length>24?v.slice(0,24)+'…':v}</a></td>`:`<td title="${v}">${v.length>24?v.slice(0,24)+'…':v}</td>`}
   return `<td class="${c=='r'?'r':''}" title="${String(v).replace(/"/g,'')}">${v}</td>`}).join('')+'</tr>').join('');
 h+='</tbody></table></div>';$('#tbl').innerHTML=h;
}
function tab(t){
 $('#tab-data').style.display=t=='data'?'':'none';
 $('#tab-issue').style.display=t=='issue'?'':'none';
 document.querySelectorAll('.tab').forEach(b=>b.classList.toggle('on',b.dataset.t==t));
}
function renderIssues(){
 $('#ibadge').textContent=ISSUES.length;
 const ORD=['미입력','사용자 준비중','접수인원 미반영','응시인원 미반영','확인필요','잔여 보강'];
 const grp={};ISSUES.forEach(i=>{(grp[i['구분']]=grp[i['구분']]||[]).push(i)});
 const keys=Object.keys(grp).sort((a,b)=>(ORD.indexOf(a)+99*(ORD.indexOf(a)<0))-(ORD.indexOf(b)+99*(ORD.indexOf(b)<0)));
 const esc=s=>String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
 let h='<div style="background:#f8fafc;border:1px solid var(--line);border-radius:10px;padding:12px 15px;margin:8px 0 14px;font-size:12.5px;line-height:1.8">'
  +'<b>읽는 법</b> — 데이터가 채워지면 항목이 자동으로 사라집니다.<br>'
  +'• <b>🧑‍💻 사용자 준비중</b>: 엑셀로 정리 중인 6개 시·군별 지역(합격선 자체가 아직 없음).<br>'
  +'• <b>△ 접수/응시인원 미반영</b>: 합격선·선발은 있으나 접수(출원)·응시인원만 일부 빈 행. 카드 안에 <b>왜 비었는지</b>와 <b>정확히 어떤 연도·직렬·대상</b>인지 다 적혀있음.<br>'
  +'• 미선발·비공개로 응시가 0인 행은 정상이라 표시 안 함.</div>';
 keys.forEach(k=>{const a=grp[k];
  h+=`<div class="igrp">${k} <span style="color:var(--mut);font-weight:400">· ${a.length}건</span></div>`;
  h+=a.map(i=>{
    const cls=k=='사용자 준비중'?'prep':(k.indexOf('미반영')>=0?'gap':'');
    let memo=esc(i['메모']||'');
    // '▷ 해당 행:' 이후는 회색 박스로
    memo=memo.replace(/\\n/g,'\n');
    const sp=memo.indexOf('▷ 해당 행:');
    let body=memo, rowsbox='';
    if(sp>=0){body=memo.slice(0,sp).trim(); rowsbox=`<span class="rows">${memo.slice(sp)}</span>`;}
    return `<div class="icard ${cls}"><div class="ihead"><span class="ireg">${i['지역']}</span><span class="ibadge2">${i['항목']}</span><span class="istat">${i['상태']}</span></div><div class="imemo">${body}${rowsbox}</div></div>`;
  }).join('');
 });
 $('#issues').innerHTML=h;
}
renderIssues();
draw();
</script></body></html>"""
html=HTML.replace("__DATA__",data).replace("__DONE__",json.dumps(done_files,ensure_ascii=False)).replace("__TOTAL__",str(TOTAL_FILES)).replace("__LINKS__",file_links).replace("__ISSUES__",issues_json)
with open(OUT,"w",encoding="utf-8") as fp: fp.write(html)
print(f"v2 생성: {OUT} | 검증행 {len(rows)} | 확인파일 {len(done_files)}")
