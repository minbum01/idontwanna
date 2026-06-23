/* 합격선 포켓북 · 공유 스크립트 (모든 페이지 공통)
   - toggleFb(): 피드백 표시/숨김
   - pbFit():   펼침면을 화면 너비에 맞게 축소 */

function toggleFb(){
  const on = document.body.classList.toggle('show-fb');
  const b = document.getElementById('fbBtn');
  if(b){
    b.classList.toggle('on', on);
    b.textContent = on ? '⚑ 피드백 숨기기 (출력 미리보기)' : '⚑ 피드백 보기';
  }
  if(!on && _typtip) _typtip.style.display = 'none';
}

/* ── 글씨 인스펙터 ── 피드백 보기 ON 상태에서 텍스트에 마우스를 올리면
   글씨크기(pt)·글씨체·굵기·B/I/U 여부를 툴팁으로 표시한다. */
let _typtip = null;
function _ensureTyptip(){
  if(_typtip) return _typtip;
  _typtip = document.createElement('div');
  _typtip.id = 'typtip';
  document.body.appendChild(_typtip);
  return _typtip;
}
function _typInfo(el){
  const cs = getComputedStyle(el);
  const pt = (parseFloat(cs.fontSize) * 72 / 96).toFixed(1);
  let fam = (cs.fontFamily.split(',')[0] || '').replace(/['"]/g,'').trim();
  if(/pretendard/i.test(fam)) fam = 'Pretendard';
  const w  = parseInt(cs.fontWeight) || 400;
  const B  = w >= 600;
  const I  = cs.fontStyle === 'italic' || cs.fontStyle === 'oblique';
  const U  = (cs.textDecorationLine || '').indexOf('underline') > -1;
  const flags = [B?'B':'', I?'I':'', U?'U':''].filter(Boolean).join('·') || '—';
  return `<b>${pt}pt</b> · ${fam} · <b>${w}</b> · ${flags}`;
}
document.addEventListener('mousemove', function(e){
  if(!document.body.classList.contains('show-fb')) return;
  const el = e.target;
  if(!el || el.id === 'typtip' || !(el.textContent||'').trim()){
    if(_typtip) _typtip.style.display = 'none';
    return;
  }
  const tip = _ensureTyptip();
  tip.innerHTML = _typInfo(el) + `<span class="tg">&lt;${el.tagName.toLowerCase()}&gt;</span>`;
  tip.style.display = 'block';
  const pad = 14;
  let x = e.clientX + pad, y = e.clientY + pad;
  const r = tip.getBoundingClientRect();
  if(x + r.width  > window.innerWidth)  x = e.clientX - r.width  - pad;
  if(y + r.height > window.innerHeight) y = e.clientY - r.height - pad;
  tip.style.left = x + 'px';
  tip.style.top  = y + 'px';
});

function pbFit(){
  const deck = document.getElementById('deck');
  if(!deck) return;
  deck.style.transform = 'none';
  const natW = deck.offsetWidth, natH = deck.offsetHeight;
  const s = Math.min(1, (window.innerWidth - 24) / natW);
  deck.style.transform = 'scale(' + s + ')';
  deck.parentElement.style.height = (natH * s) + 'px';
}

window.addEventListener('resize', pbFit);
window.addEventListener('load', pbFit);
document.addEventListener('DOMContentLoaded', pbFit);
/* 웹폰트 로딩 후 높이 재계산 */
if(document.fonts && document.fonts.ready){ document.fonts.ready.then(pbFit); }
setTimeout(pbFit, 400);
