(function(){
  var sid=Math.random().toString(36).slice(2)+Date.now().toString(36), r=null;
  try{r=new URLSearchParams(location.search).get('r'); if(r)localStorage.setItem('ms-r',r); else r=localStorage.getItem('ms-r');}catch(e){}
  window.__msSid=sid; window.__msR=r;
  var els=[].slice.call(document.querySelectorAll('header[id],section[id],footer[id]'));
  var secs={}, clicks=[], cur=els[0]?els[0].id:'page', last=Date.now();
  ['scroll','mousemove','keydown','touchstart','pointerdown'].forEach(function(ev){addEventListener(ev,function(){last=Date.now();},{passive:true});});
  function here(){var mid=innerHeight/2; for(var i=0;i<els.length;i++){var b=els[i].getBoundingClientRect(); if(b.top<=mid&&b.bottom>mid)return els[i].id;} return cur;}
  // a second counts only while the tab is visible and the reader moved in the last 2 minutes
  setInterval(function(){ if(document.visibilityState!=='visible'||Date.now()-last>120000)return; cur=here(); secs[cur]=(secs[cur]||0)+1; window.__msSecs=(window.__msSecs||0)+1; },1000);
  function send(type){
    var items=[]; for(var k in secs)items.push({section:k,secs:secs[k]});
    if(type!=='open'&&!items.length&&!clicks.length)return;
    var body=JSON.stringify({type:type,sid:sid,r:r,ref:document.referrer,vw:innerWidth,at:cur,items:items,clicks:clicks});
    secs={}; clicks=[];
    try{ if(navigator.sendBeacon&&navigator.sendBeacon('/api/t',new Blob([body],{type:'application/json'})))return; }catch(e){}
    try{fetch('/api/t',{method:'POST',headers:{'Content-Type':'application/json'},body:body,keepalive:true});}catch(e){}
  }
  send('open');
  setInterval(function(){send('dwell');},10000);
  document.addEventListener('visibilitychange',function(){if(document.visibilityState==='hidden')send('dwell');});
  addEventListener('pagehide',function(){send('dwell');});
  document.addEventListener('click',function(e){var a=e.target.closest&&e.target.closest('a[href]'); if(!a)return; var h=a.getAttribute('href'); if(/^(https?:|mailto:)/.test(h)){cur=here(); clicks.push(a.href); send('dwell');}},true);
})();
