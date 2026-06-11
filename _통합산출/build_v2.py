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
_agg=_dd(lambda:[0,0,0])
for r in rows:
    a=_agg[(r['지역'],r['시험종류'])]; a[0]+=1
    if r['경쟁률(접수/선발)'].strip(): a[1]+=1
    if r['경쟁률(응시/선발)'].strip(): a[2]+=1
for (_reg,_jt),a in sorted(_agg.items()):
    if a[1]<a[0]: issues.append({'구분':'접수 미보강','지역':_reg,'항목':_jt+' 경쟁률(접수)','상태':f'△ {a[1]}/{a[0]}','메모':'접수 일부 미반영 또는 원본 부재'})
    if a[2]<a[0]: issues.append({'구분':'응시 미보강','지역':_reg,'항목':_jt+' 경쟁률(응시)','상태':f'△ {a[2]}/{a[0]}','메모':'응시 일부 미반영 또는 원본 부재'})
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
 const ORD=['미입력','확인필요','원본없음','접수 미보강','응시 미보강','잔여 보강','사용자 준비중'];
 const grp={};ISSUES.forEach(i=>{(grp[i['구분']]=grp[i['구분']]||[]).push(i)});
 const keys=Object.keys(grp).sort((a,b)=>(ORD.indexOf(a)+99*(ORD.indexOf(a)<0))-(ORD.indexOf(b)+99*(ORD.indexOf(b)<0)));
 let h='<p class="sub" style="margin:6px 0 10px">처리하면서 막히거나 미뤄둔 항목입니다. 데이터가 채워지면 자동으로 사라집니다.</p>';
 keys.forEach(k=>{const a=grp[k];
  h+=`<div class="igrp">${k} <span style="color:var(--mut);font-weight:400">(${a.length})</span></div>`;
  h+='<table class="itbl"><thead><tr><th style="width:70px">지역</th><th style="width:120px">상태</th><th style="width:200px">항목</th><th>사유/메모</th></tr></thead><tbody>';
  h+=a.map(i=>`<tr><td><b>${i['지역']}</b></td><td>${i['상태']}</td><td>${i['항목']}</td><td style="color:var(--mut)">${i['메모']||''}</td></tr>`).join('');
  h+='</tbody></table>';
 });
 $('#issues').innerHTML=h;
}
renderIssues();
draw();
</script></body></html>"""
html=HTML.replace("__DATA__",data).replace("__DONE__",json.dumps(done_files,ensure_ascii=False)).replace("__TOTAL__",str(TOTAL_FILES)).replace("__LINKS__",file_links).replace("__ISSUES__",issues_json)
with open(OUT,"w",encoding="utf-8") as fp: fp.write(html)
print(f"v2 생성: {OUT} | 검증행 {len(rows)} | 확인파일 {len(done_files)}")
