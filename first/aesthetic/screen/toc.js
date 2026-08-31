/* dh-toc */
(function(){
 if(window.__dhToc)return; window.__dhToc=1;
 /* Measured, never typed: the bar grew a title row and a key, so any constant
    here goes stale and the active section is decided against the wrong band. */
 function barHeight(){
  var bar=document.querySelector('.dh-toc');
  return bar?Math.round(bar.getBoundingClientRect().height)+8:64;
 }
 function scroller(){
  return document.querySelector('.main') || document.scrollingElement || document.documentElement;
 }
 function start(){
  var links=[].slice.call(document.querySelectorAll('.dh-toc a[data-zone]'));
  var zones=links.map(function(a){return document.getElementById(a.getAttribute('href').slice(1))})
                 .filter(Boolean);
  if(!zones.length)return;
  function mark(id){links.forEach(function(a){
   a.setAttribute('aria-current', a.getAttribute('href')==='#'+id ? 'true':'false');});}
  mark(zones[0].id);
  /* Clicking a pill marks it AT ONCE. Leaving it to the observer meant the
     indicator lagged the click by a scroll -- which reads as a broken nav,
     because the thing you just pressed is not the thing lit up. */
  links.forEach(function(a){a.addEventListener('click',function(e){
   var id=a.getAttribute('href').slice(1);
   var zone=document.getElementById(id);
   mark(id);
   if(!zone)return;
   e.preventDefault();
   var root=scroller();
   var top=zone.getBoundingClientRect().top + root.scrollTop - barHeight();
   root.scrollTo({top:Math.max(0,top), behavior:'smooth'});
  });});
  /* Highest section still intersecting the top band wins. Picking the largest
     visible ratio instead makes a short section that is fully on screen beat
     the long one the reader is actually inside. */
  if(!('IntersectionObserver' in window))return;
  var visible={};
  var rootEl=document.querySelector('.main');
  var io=new IntersectionObserver(function(entries){
   entries.forEach(function(e){visible[e.target.id]=e.isIntersecting});
   for(var i=0;i<zones.length;i++){ if(visible[zones[i].id]){ mark(zones[i].id); return } }
  },{root:rootEl, rootMargin:'-'+barHeight()+'px 0px -68% 0px', threshold:0});
  zones.forEach(function(z){io.observe(z)});
  /* The second level tracks headings, not sections, so it needs its own
     observer -- sharing one made a heading scrolling past re-mark the zone. */
  var subs=[].slice.call(document.querySelectorAll('.dh-subnav a[data-sub]'));
  var heads=subs.map(function(a){return document.getElementById(a.getAttribute('href').slice(1))})
                .filter(Boolean);
  if(!heads.length)return;
  function markSub(id){subs.forEach(function(a){
   a.setAttribute('aria-current', a.getAttribute('href')==='#'+id ? 'true':'false');});}
  markSub(heads[0].id);
  var vis={};
  var io2=new IntersectionObserver(function(entries){
   entries.forEach(function(e){vis[e.target.id]=e.isIntersecting});
   for(var i=heads.length-1;i>=0;i--){ if(vis[heads[i].id]){ markSub(heads[i].id); return } }
  },{rootMargin:'-100px 0px -60% 0px', threshold:0});
  heads.forEach(function(h){io2.observe(h)});
 }
 function measure(){
  var bar=document.querySelector('.dh-toc'); if(!bar)return;
  var art=document.querySelector('.dh-art'); if(!art)return;
  art.style.setProperty('--dh-toc-h', Math.round(bar.getBoundingClientRect().height)+'px');
 }
 if(document.readyState==='loading')
  document.addEventListener('DOMContentLoaded',function(){measure();start()});
 else {measure();start()}
 window.addEventListener('resize',measure);
})();
