/* dh-rehydrate */
(function(){
 if(window.__dhRehydrated)return; window.__dhRehydrated=1;
 /* The socket is the only store. The screen is a snapshot `embed` baked, and
    the server already pushes the ledger's own reduction on connect and every
    decision after it -- so a browser-local cache adds a second opinion and no
    information. The one that used to live here read its revision stamp before
    the rows were parsed, wrote every entry under an empty revision, and threw
    the whole cache away on the next load: three layers of sync that had never
    once been read back. Everything that worked was this socket. */
 /* Confirmation on the ROUND TRIP, not on the click. The score is written by
    the companion and echoed back; flashing "saved" on mousedown would promise
    something the ledger has not agreed to yet -- and a dropped socket is
    exactly when the user most needs to know it did not save. */
 function flashSaved(row){
  var strip=row.querySelector('.dh-signals'); if(!strip)return;
  var host=document.querySelector('[data-saved]');
  var tag=row.querySelector('.dh-saved');
  if(!tag){tag=document.createElement('span'); tag.className='dh-saved';
           tag.setAttribute('role','status'); strip.appendChild(tag);}
  tag.textContent=(host&&host.getAttribute('data-saved'))||'Saved';
  tag.setAttribute('data-on','1');
  tag.removeAttribute('data-cheer');
  clearTimeout(tag.__dhT);
  tag.__dhT=setTimeout(function(){tag.removeAttribute('data-on')},2400);
 }
 function paint(row,s,live){
  if(live)flashSaved(row);
  if(typeof s.stars==='number'){
   row.dataset.stars=String(s.stars); row.dataset.scored='yes';
   /* The readout is CSS reading attr() off the strip, so the strip needs the
      value too -- without this the number stayed at whatever was baked into
      the page and only a refresh corrected it. */
   var strip=row.querySelector('.dh-stars');
   if(strip){strip.dataset.stars=String(s.stars); strip.dataset.scored='yes';}
   row.querySelectorAll('[data-rank]').forEach(function(b){
    var n=parseInt(b.dataset.rank,10);
    b.classList.toggle('on', n===0 ? s.stars===0 : (n>0&&n<=s.stars));});
  }
  if('sentiment' in s) row.querySelectorAll('[data-sentiment]').forEach(function(b){
    b.classList.toggle('on', b.dataset.sentiment===s.sentiment);});
  if('bookmark' in s) row.querySelectorAll('[data-bookmark]').forEach(function(b){
    b.classList.toggle('on', !!s.bookmark);});
  if('verdict' in s){
   row.querySelectorAll('[data-verdict]').forEach(function(b){
    b.classList.toggle('on', b.dataset.verdict===s.verdict);});
   /* Marking something done is the one act on this page that feels final, so
      it says so louder than a rank does. */
   if(s.verdict==='completed'){
    row.setAttribute('data-done','1');
    setTimeout(function(){row.removeAttribute('data-done')},800);
    var t=row.querySelector('.dh-saved'), h=document.querySelector('[data-cheer-text]');
    if(t){t.setAttribute('data-cheer','1');
          t.textContent=(h&&h.getAttribute('data-cheer-text'))||t.textContent;}
   }
  }
  try{document.dispatchEvent(new CustomEvent('dh-row-painted',
    {detail:{element:row.getAttribute('data-element')}}));}catch(e){}
 }
 function rowFor(el){
  var all=document.querySelectorAll('.dh-fb[data-element]');
  for(var i=0;i<all.length;i++) if(all[i].getAttribute('data-element')===el) return all[i];
  return null;}
 /* The greeting routinely beats DOMContentLoaded, and a state applied to rows
    that do not exist yet is silently lost. Hold it until they do. */
 var ready=false, pending={};
 function applyState(st,live){
  Object.keys(st).forEach(function(el){
   var s=st[el]; if(!s)return;
   if(!ready){pending[el]=s; return}
   var row=rowFor(el); if(row)paint(row,s,live);});}
 function boot(){ready=true; var q=pending; pending={}; applyState(q);}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);
 else boot();
 function fold(ev){
  if(!ev||!ev.element)return;
  var s={};
  if(ev.reset===true||ev.type==='reset')s.stars=0;
  else if(typeof ev.stars==='number')s.stars=ev.stars;
  if('sentiment' in ev)s.sentiment=ev.sentiment;
  if(ev.verdict==='completed'||ev.verdict==='approved')s.verdict='completed';
  else if(ev.verdict==='proposed'||ev.verdict==='rejected')s.verdict=null;
  if('bookmark' in ev)s.bookmark=!!ev.bookmark;
  var one={}; one[ev.element]=s; applyState(one,true);}
 /* Ranks and thumbs are the companion's to send, and the server echoes them
    back here. The completed toggle is NOT: a companion that only recognises
    its own verdict words drops the click before anything is sent -- no DOM
    change, no event, nothing in the ledger -- and the box simply refused to
    tick. This skill owns its own vocabulary, so it delivers this one itself
    rather than hoping the companion happens to share it. */
 var sock=null;
 document.addEventListener('click',function(e){
  var btn=e.target.closest?e.target.closest('[data-verdict]'):null; if(!btn)return;
  var row=btn.closest('.dh-fb[data-element]'); if(!row)return;
  if(!sock||sock.readyState!==1)return;
  var on=btn.classList.contains('on');
  sock.send(JSON.stringify({type:'verdict',element:row.getAttribute('data-element'),
   choice:row.getAttribute('data-element'),
   verdict:on?'proposed':(btn.getAttribute('data-verdict')||'completed'),
   text:row.getAttribute('data-label')||null,timestamp:Date.now()}));
 },true);
 /* A 4th vocabulary word the companion does not know either -- same reason
    as `completed` above: deliver it directly instead of hoping helper.js
    happens to recognise "bookmark". */
 document.addEventListener('click',function(e){
  var btn=e.target.closest?e.target.closest('[data-bookmark]'):null; if(!btn)return;
  var row=btn.closest('.dh-fb[data-element]'); if(!row)return;
  if(!sock||sock.readyState!==1)return;
  var on=btn.classList.contains('on');
  sock.send(JSON.stringify({type:'bookmark',element:row.getAttribute('data-element'),
   choice:row.getAttribute('data-element'),
   bookmark:!on,
   text:row.getAttribute('data-label')||null,timestamp:Date.now()}));
 },true);
 (function socket(){
  var ws;
  try{ws=new WebSocket((location.protocol==='https:'?'wss://':'ws://')+location.host+'/')}
  catch(e){return}
  sock=ws;
  ws.onmessage=function(e){
   var m; try{m=JSON.parse(e.data)}catch(_){return}
   if(m&&m.type==='dh-signal')fold(m.event);
   else if(m&&m.type==='dh-state'&&m.state)applyState(m.state);};
  ws.onclose=function(){sock=null;setTimeout(socket,1500)};
 })();
})();
