/* dh-lightbox */
(function(){
 if(window.__dhLb)return; window.__dhLb=1;
 var lb,slides=[],at=0,lastFocus=null;
 function rows(){
  var seen={},out=[];
  [].forEach.call(document.querySelectorAll('.dh-art .dh-fb[data-element]'),function(r){
   var id=r.getAttribute('data-element');
   if(seen[id]||r.classList.contains('dh-fb-before'))return;
   if(r.closest('.dh-spec-score')||!r.querySelector('.dh-shot'))return;
   seen[id]=1; out.push(r);
  });
  return out;
 }
 function findRow(id){
  var nodes=document.querySelectorAll('.dh-art .dh-fb[data-element="'+CSS.escape(id)+'"]');
  for(var i=0;i<nodes.length;i++){
   if(!nodes[i].closest('.dh-spec-score'))return nodes[i];
  }
  return null;
 }
 function slidesFor(id){
  var row=findRow(id);
  if(!row)return rows();
  var zone=row.closest('.dh-zone[data-zone]');
  if(!zone)return [row];
  var out=[];
  zone.querySelectorAll('.dh-fb[data-element]').forEach(function(r){
   if(r.closest('.dh-spec-score')||!r.querySelector('.dh-shot'))return;
   out.push(r);
  });
  return out.length?out:[row];
 }
 function wireProxy(node, sel){
  node.setAttribute('data-proxy', sel);
  node.setAttribute('role','button');
  node.setAttribute('tabindex','0');
 }
 function cloneSignals(row, wrap){
  var sig=row.querySelector('.dh-signals');
  if(!sig)return;
  var box=document.createElement('div'); box.className='dh-lb-score';
  var shell=document.createElement('div'); shell.className='dh-fb dh-lb-fb';
  var c=sig.cloneNode(true);
  c.querySelectorAll('[data-rank]').forEach(function(n){
   wireProxy(n, '.dh-stars [data-rank="'+n.getAttribute('data-rank')+'"]');
  });
  c.querySelectorAll('[data-sentiment]').forEach(function(n){
   wireProxy(n, '[data-sentiment="'+n.getAttribute('data-sentiment')+'"]');
  });
  c.querySelectorAll('[data-verdict]').forEach(function(n){
   wireProxy(n, '[data-verdict="'+n.getAttribute('data-verdict')+'"]');
  });
  c.querySelectorAll('[data-bookmark]').forEach(function(n){
   wireProxy(n, '[data-bookmark]');
  });
  shell.appendChild(c); box.appendChild(shell); wrap.appendChild(box);
 }
 function indexOf(id){
  for(var i=0;i<slides.length;i++){
   if(slides[i].getAttribute('data-element')===id)return i;
  }
  return -1;
 }
 function txt(el,sel){var n=el.querySelector(sel);return n?n.textContent.trim():''}
 function prepShotClone(node){
  var c=node.cloneNode(true);
  c.removeAttribute('style');
  c.className='dh-shot';
  return c;
 }
 function fitShotInner(shot){
  if(window.__dhFitShotInner) return window.__dhFitShotInner(shot);
 }
 function build(){
  lb=document.createElement('dialog');
  lb.className='dh-lb';
  if('closedBy' in HTMLDialogElement.prototype) lb.setAttribute('closedby','any');
  lb.setAttribute('aria-labelledby','dh-lb-title');
  lb.innerHTML=
   '<div class="dh-lb-shell">'+
   '<div class="dh-lb-bar"><span class="dh-lb-count"></span>'+
   '<span class="dh-lb-name"><b class="dh-lb-id" id="dh-lb-title"></b></span>'+
   '<span class="dh-lb-state"></span>'+
   '<button class="dh-lb-x" type="button" aria-label="Cerrar">&#10005;</button></div>'+
   '<div class="dh-lb-body"><div class="dh-lb-frame">'+
   '<button class="dh-lb-nav" data-step="-1" type="button" aria-label="Anterior">&#8249;</button>'+
   '<div class="dh-lb-art"></div>'+
   '<button class="dh-lb-nav" data-step="1" type="button" aria-label="Siguiente">&#8250;</button>'+
   '</div><div class="dh-lb-copy"></div></div>'+
   '<div class="dh-lb-foot"><div class="dh-lb-score-wrap"></div></div>'+
   '<div class="dh-lb-strip"></div></div>';
  document.body.appendChild(lb);
  lb.querySelector('.dh-lb-x').addEventListener('click',close);
  lb.addEventListener('close',function(){
   if(lastFocus&&lastFocus.focus)lastFocus.focus();
  });
  lb.addEventListener('click',function(e){
   if(!e.target.closest('.dh-lb-shell')){close();return}
   var nav=e.target.closest('.dh-lb-nav'); if(nav){go(at+ +nav.getAttribute('data-step'));return}
   var th=e.target.closest('.dh-lb-strip .dh-shot');
   if(th){go(indexOf(th.getAttribute('data-el')));return}
   var prox=e.target.closest('[data-proxy]');
   if(prox){
    var row=slides[at]; if(!row)return;
    var real=row.querySelector(prox.getAttribute('data-proxy'));
    if(real){real.click(); setTimeout(function(){paint()},0)}
    return;
   }
  });
  document.addEventListener('keydown',function(e){
   if(!lb.open)return;
   if(e.key==='Escape'){close();return}
   if(e.key==='ArrowLeft'){go(at-1)}
   else if(e.key==='ArrowRight'){go(at+1)}
  });
 }
 function paint(){
  var row=slides[at]; if(!row)return;
  var id=row.getAttribute('data-element');
  lb.querySelector('.dh-lb-count').textContent=(at+1)+' / '+slides.length;
  var titled=row.querySelector('.dh-id');
  lb.querySelector('.dh-lb-id').textContent=titled?titled.textContent.trim():id;
  lb.querySelector('.dh-lb-state').textContent=txt(row,'.dh-state');
  var shot=row.querySelector('.dh-shot');
  var art=lb.querySelector('.dh-lb-art'); art.innerHTML='';
  if(shot){var c=prepShotClone(shot); art.appendChild(c); fitShotInner(c)}
  var side=lb.querySelector('.dh-lb-copy'); side.innerHTML='';
  var why=row.querySelector('.dh-desc:not(.dh-sub)');
  if(why){var p=document.createElement('p'); p.className='dh-lb-why';
          p.textContent=why.textContent.trim(); side.appendChild(p)}
  [].forEach.call(row.querySelectorAll('.dh-desc.dh-sub'),function(d){
   var p=document.createElement('p'); p.className='dh-lb-sub';
   var b=d.querySelector('b');
   p.innerHTML='<b></b>'; p.querySelector('b').textContent=b?b.textContent.trim():'';
   p.appendChild(document.createTextNode(
     d.textContent.replace(b?b.textContent:'','').trim()));
   side.appendChild(p);
  });
  var scoreWrap=lb.querySelector('.dh-lb-score-wrap'); scoreWrap.innerHTML='';
  cloneSignals(row, scoreWrap);
  var st=lb.querySelector('.dh-lb-strip'); st.innerHTML='';
  slides.forEach(function(r,i){
   var s=r.querySelector('.dh-shot'); if(!s)return;
   var c=prepShotClone(s); c.setAttribute('data-el',r.getAttribute('data-element'));
   if(i===at)c.setAttribute('aria-current','true');
   fitShotInner(c);
   st.appendChild(c);
  });
  var cur=st.querySelector('[aria-current="true"]');
  if(cur&&cur.scrollIntoView)cur.scrollIntoView({block:'nearest',inline:'center'});
  lb.querySelector('[data-step="-1"]').disabled = at<=0;
  lb.querySelector('[data-step="1"]').disabled = at>=slides.length-1;
 }
 function go(i){ if(i<0||i>=slides.length)return; at=i; paint() }
 function open(id){
  slides=slidesFor(id); var i=indexOf(id);
  if(i<0)return;
  lastFocus=document.activeElement;
  at=i;
  if(typeof lb.showModal==='function') lb.showModal();
  paint();
  requestAnimationFrame(function(){
   var art=lb.querySelector('.dh-lb-art .dh-shot');
   if(art)fitShotInner(art);
   lb.querySelectorAll('.dh-lb-strip .dh-shot').forEach(function(s){fitShotInner(s)});
  });
  lb.querySelector('.dh-lb-x').focus();
 }
 function close(){
  if(lb.open) lb.close();
  if(lastFocus&&lastFocus.focus)lastFocus.focus();
 }
 function start(){
  build();
  window.__dhOpenSlide=open;
  document.addEventListener('click',function(e){
   var s=e.target.closest('.dh-art .dh-shot[data-el]');
   if(s){e.preventDefault(); open(s.getAttribute('data-el')); return}
   var bar=e.target.closest('.dh-temp a[data-el]');
   if(bar){e.preventDefault(); open(bar.getAttribute('data-el'))}
  });
  chartCard();
  document.addEventListener('dh-row-painted',function(e){
   if(!lb.open||!e.detail||!e.detail.element)return;
   var row=slides[at]; if(!row||row.getAttribute('data-element')!==e.detail.element)return;
   paint();
  });
 }
 function chartCard(){
  var card=document.createElement('div');
  card.className='dh-chartcard'; card.setAttribute('aria-hidden','true');
  document.body.appendChild(card);
  var hide=function(){card.removeAttribute('data-on')};
  function show(bar){
   var id=bar.getAttribute('data-el'); if(!id)return;
   var row=null, all=document.querySelectorAll('.dh-art .dh-fb[data-element]');
   for(var i=0;i<all.length;i++){
    if(all[i].getAttribute('data-element')===id && !all[i].closest('.dh-spec-score')){row=all[i];break}
   }
   var shot=row&&row.querySelector('.dh-shot');
   card.innerHTML='';
   if(shot){var c=prepShotClone(shot); card.appendChild(c); fitShotInner(c)}
   var name=document.createElement('b');
   name.textContent=bar.getAttribute('data-name')||id;
   card.appendChild(name);
   var meta=document.createElement('span');
   var score=bar.getAttribute('data-score');
   meta.textContent=(score==='--'?'':score+'/5');
   card.appendChild(meta);
   card.setAttribute('data-on','1');
   var r=bar.getBoundingClientRect(), w=210;
   var left=Math.min(Math.max(8,r.left+r.width/2-w/2), innerWidth-w-8);
   card.style.left=left+'px';
   card.style.top=Math.min(r.bottom+10, innerHeight-card.offsetHeight-8)+'px';
  }
  document.addEventListener('pointerover',function(e){
   var bar=e.target.closest&&e.target.closest('.dh-temp a[data-el]');
   if(bar)show(bar); else if(!e.target.closest||!e.target.closest('.dh-chartcard'))hide();
  });
  document.addEventListener('focusin',function(e){
   var bar=e.target.closest&&e.target.closest('.dh-temp a[data-el]');
   if(bar)show(bar); else hide();
  });
  window.addEventListener('scroll',hide,{passive:true});
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start);
 else start();
})();
