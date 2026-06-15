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
}

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
