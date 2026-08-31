/* dh-shot-fit */
(function(){
 if(window.__dhShotFit)return; window.__dhShotFit=1;
 /* Card thumbnails use the same scale math as the slideshow. Pure CSS
    `transform:scale(calc(var(--dh-shot-w)/510))` on a 510×660 absolutely
    positioned inner gets clipped by `overflow:hidden` before the transform
    is accounted for -- grey boxes in the row, full drawings in the modal. */
 function fitShotInner(shot){
  var inner=shot.querySelector('.dh-shot-inner');
  if(!inner)return;
  var cw=parseFloat(inner.getAttribute('data-comp-w'))||510;
  var ch=parseFloat(inner.getAttribute('data-comp-h'))||660;
  function apply(){
   var w=shot.clientWidth, h=shot.clientHeight;
   if(w<1||h<1)return;
   var s=Math.min(w/cw, h/ch);
   inner.style.transform='scale('+s+')';
   inner.style.inlineSize=cw+'px';
   inner.style.blockSize=ch+'px';
   inner.style.transformOrigin='0 0';
   inner.style.position='absolute';
   inner.style.insetBlockStart=((h-ch*s)/2)+'px';
   inner.style.insetInlineStart=((w-cw*s)/2)+'px';
   inner.style.pointerEvents='none';
  }
  apply();
  if(shot._dhRo)shot._dhRo.disconnect();
  if(typeof ResizeObserver!=='undefined'){
   var ro=new ResizeObserver(apply);
   ro.observe(shot);
   shot._dhRo=ro;
  }
 }
 window.__dhFitShotInner=fitShotInner;
 function fitAll(root){
  (root||document).querySelectorAll('.dh-shot-inner').forEach(function(inner){
   var shot=inner.closest('.dh-shot');
   if(shot)fitShotInner(shot);
  });
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',function(){fitAll()});
 else fitAll();
})();
