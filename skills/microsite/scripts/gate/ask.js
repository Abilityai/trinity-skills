// Soft gate: the page is open; after ASK_AFTER active seconds a small card asks for an
// email. Never blocks reading, closes on one click, asks at most once per visit.
(function(){
  var ASK_AFTER=45, shown=false;
  function get(s,k){try{return s.getItem(k);}catch(e){return null;}}
  function set(s,k){try{s.setItem(k,'1');}catch(e){}}
  if(get(localStorage,'ms-known')||get(sessionStorage,'ms-asked'))return;
  var timer=setInterval(function(){
    if(shown||(window.__msSecs||0)<ASK_AFTER)return;
    shown=true; clearInterval(timer);
    fetch('/api/gate').then(function(r){return r.json();}).then(function(j){ if(j&&j.known)set(localStorage,'ms-known'); else show(); }).catch(show);
  },1000);
  function show(){
    set(sessionStorage,'ms-asked');
    var css=document.createElement('style');
    css.textContent='#ms-ask{position:fixed;right:16px;bottom:16px;z-index:60;width:min(360px,calc(100vw - 32px));background:var(--bg-1,#131318);color:var(--ink,#fff);border:1px solid var(--line,#34343C);border-radius:14px;padding:18px 18px 16px;box-shadow:0 12px 40px rgba(0,0,0,.35);font:15px/1.5 "DM Sans",system-ui,sans-serif;opacity:0;transform:translateY(10px);transition:opacity .35s,transform .35s}'
      +'#ms-ask.on{opacity:1;transform:none}'
      +'#ms-ask b{display:block;font-size:16px;margin:0 28px 4px 0}'
      +'#ms-ask p{margin:0 0 12px;color:var(--ink-dim,#9DA2BC)}'
      +'#ms-ask form{display:flex;gap:8px}'
      +'#ms-ask input{flex:1;min-width:0;font:inherit;color:inherit;background:var(--bg,#0B0B0E);border:1px solid var(--line,#34343C);border-radius:9px;padding:10px 12px}'
      +'#ms-ask button{font:inherit;font-weight:700;cursor:pointer;border:0;border-radius:9px}'
      +'#ms-ask .go{color:#fff;background:var(--accent,#B85050);padding:10px 16px}'
      +'#ms-ask .x{position:absolute;top:8px;right:8px;width:32px;height:32px;background:none;color:var(--ink-mute,#6B6E80);font-size:20px;line-height:1}'
      +'#ms-ask input:focus-visible,#ms-ask button:focus-visible{outline:2px solid var(--accent,#B85050);outline-offset:2px}'
      +'#ms-ask .err{min-height:0;margin:8px 0 0;font-size:13.5px;color:var(--risk,#FF8FAB)}'
      +'@media (prefers-reduced-motion:reduce){#ms-ask{transition:none}}'
      +'@media print{#ms-ask{display:none}}';
    document.head.appendChild(css);
    var box=document.createElement('aside');
    box.id='ms-ask'; box.setAttribute('aria-label','Stay in touch');
    box.innerHTML='<button class="x" type="button" aria-label="Close">&times;</button>'
      +'<b>Thanks for reading.</b>'
      +'<p>If you would like us to follow up, leave your email. Or just keep reading.</p>'
      +'<form novalidate><input type="email" name="email" autocomplete="email" inputmode="email" placeholder="you@company.com" aria-label="Your email">'
      +'<button class="go" type="submit">Send</button></form><p class="err" role="alert"></p>';
    document.body.appendChild(box);
    requestAnimationFrame(function(){box.classList.add('on');});
    var f=box.querySelector('form'), em=f.querySelector('input'), err=box.querySelector('.err'), go=f.querySelector('.go');
    function close(){box.classList.remove('on'); setTimeout(function(){box.remove();},400);}
    box.querySelector('.x').addEventListener('click',close);
    f.addEventListener('submit',function(e){
      e.preventDefault(); err.textContent='';
      var v=em.value.trim();
      if(!/^[^\s@]+@[^\s@]+\.[A-Za-z]{2,}$/.test(v)){err.textContent='That does not look like an email address.'; em.focus(); return;}
      go.disabled=true;
      fetch('/api/gate',{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({email:v,sid:window.__msSid,r:window.__msR,ref:document.referrer})}).then(function(res){
        if(!res.ok)throw 0;
        set(localStorage,'ms-known');
        box.innerHTML='<b>Thank you.</b><p style="margin:0">We will be in touch.</p>';
        setTimeout(close,2500);
      }).catch(function(){err.textContent='Could not save that. Try again.'; go.disabled=false;});
    });
  }
})();
