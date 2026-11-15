/* Message state stays in this tab. Only enable/disable settings use storage. */
(() => {
  'use strict';
  const adapter=globalThis.PrivacyGateSelectors[location.hostname];
  if(!adapter)return;
  const {detect}=globalThis.PrivacyGateDetector;
  const {policies,categories}=globalThis.PrivacyGatePolicy;
  const rules=policies['AI Chatbot'];
  const host=document.createElement('div');
  host.id='privacygate-review';
  const shadow=host.attachShadow({mode:'closed'});
  const style=document.createElement('style');
  style.textContent=':host{all:initial;position:fixed;right:16px;bottom:16px;z-index:2147483647;font:14px/1.5 system-ui;color:#17201f}button{font:inherit;min-height:44px;padding:8px 12px;margin:4px;border:1px solid #687a72;border-radius:8px;background:#fff;color:#152b24;cursor:pointer}button:focus-visible{outline:3px solid #1b8061;outline-offset:2px}button:disabled{opacity:.6}section{width:min(360px,calc(100vw - 48px));max-height:65vh;overflow:auto;background:#fff;border:1px solid #687a72;border-radius:12px;padding:12px;box-shadow:0 8px 32px #0003}p{margin:8px 0;overflow-wrap:anywhere}textarea{width:95%;min-height:100px}[hidden]{display:none}';
  shadow.append(style);
  const make=(tag,text,parent=shadow)=>{const el=document.createElement(tag);if(text)el.textContent=text;parent.append(el);return el;};
  const badge=make('button','PrivacyGate starting…');badge.type='button';badge.setAttribute('aria-expanded','false');
  const status=make('p','');status.setAttribute('role','status');status.setAttribute('aria-live','polite');
  const panel=make('section');panel.hidden=true;panel.setAttribute('aria-label','PrivacyGate message review');
  const title=make('strong','Review before sending',panel);
  make('p','Local patterns only. Names, schools, places and personal stories are not checked. No match is not a privacy guarantee.',panel);
  const list=make('div','',panel);
  const controls=make('div','',panel);
  const addButton=(text,fn,parent=controls)=>{const b=make('button',text,parent);b.type='button';b.onclick=fn;return b;};
  const fallback=make('textarea','',panel);fallback.readOnly=true;fallback.hidden=true;fallback.setAttribute('aria-label','Fixed text for manual copy');
  const copy=addButton('Copy fixed text',async()=>{try{await navigator.clipboard.writeText(fallback.value);status.textContent='Fixed text copied. Paste it into the composer and review again.';}catch{fallback.hidden=false;fallback.focus();fallback.select();status.textContent='Clipboard unavailable. Select and copy the fixed text.';}});copy.hidden=true;
  let enabled=false, settingsReady=false, pending=null, permit=null, timer=null;
  const visible=el=>el&&el.getClientRects().length>0;
  const find=selectors=>selectors.flatMap(s=>[...document.querySelectorAll(s)]).find(visible);
  const composer=()=>find(adapter.composer);
  const sendButton=()=>find(adapter.send);
  const read=el=>el?.tagName==='TEXTAREA'?el.value:(el?.innerText??'');
  const action=f=>rules[f.category]??'BLOCK';
  const summarize=fs=>({block:fs.filter(f=>action(f)==='BLOCK').length,warn:fs.filter(f=>action(f)==='WARN').length});
  const hide=()=>{panel.hidden=true;badge.setAttribute('aria-expanded','false');pending=null;permit=null;list.replaceChildren();fallback.value='';fallback.hidden=true;copy.hidden=true;};
  function refresh(){
    if(!settingsReady){badge.textContent='PrivacyGate loading settings…';return;}
    if(!enabled){badge.textContent='PrivacyGate disabled on this site';return;}
    const el=composer();
    if(!el||!sendButton()){badge.textContent='PrivacyGate inactive on this page';return;}
    try{const counts=summarize(detect(read(el)));badge.textContent=`PrivacyGate · ${counts.block} blocked · ${counts.warn} to review`;}
    catch{badge.textContent='PrivacyGate check unavailable — do not rely on this check';}
  }
  const mask=value=>value.length>4?value.slice(0,2)+'…'+value.slice(-2):'••••';
  function show(){
    panel.hidden=false;badge.setAttribute('aria-expanded','true');list.replaceChildren();
    const el=composer();
    if(!settingsReady||!enabled||!el||!sendButton()){make('p','PrivacyGate is inactive here. Review your message manually.',list);return;}
    let findings;
    try{findings=detect(read(el));}catch{make('p','Validation unavailable. Review manually; sending was stopped.',list);return;}
    if(!findings.length)make('p','No supported patterns found. Review the message yourself.',list);
    findings.forEach((f,index)=>{
      const row=make('div','',list);
      make('p',`${categories[f.category]?.label??'Sensitive detail'} · ${action(f)} · ${mask(f.matched_text)}`,row);
      addButton('Fix',()=>fix(index),row);
    });
    override.hidden=!pending;
    override.textContent=summarize(findings).block?'Send anyway':'Send with warning';
  }
  function fix(index=null){
    const el=composer();if(!enabled||!el)return;
    try{
      const original=read(el), all=detect(original);
      const selected=index===null?all.filter(f=>action(f)!=='ALLOW'):[all[index]].filter(Boolean);
      const mappings=new Map();let fixed=original;
      for(const f of selected){
        const key=f.category+'\0'+f.matched_text;if(mappings.has(key))continue;
        const prefix=categories[f.category]?.placeholder??'DETAIL';let n=1;
        while(original.includes(`[${prefix}_${n}]`)||[...mappings.values()].includes(`[${prefix}_${n}]`))n++;
        mappings.set(key,`[${prefix}_${n}]`);
      }
      for(const f of [...selected].reverse())fixed=fixed.slice(0,f.start)+mappings.get(f.category+'\0'+f.matched_text)+fixed.slice(f.end);
      pending=null;permit=null;
      let succeeded=false;
      try{
        el.focus();
        if(el.tagName==='TEXTAREA'){
          const setter=Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set;
          setter.call(el,fixed);el.dispatchEvent(new Event('input',{bubbles:true}));succeeded=read(el)===fixed;
        }else{
          const range=document.createRange();range.selectNodeContents(el);
          const selection=window.getSelection();selection.removeAllRanges();selection.addRange(range);
          succeeded=document.execCommand('insertText',false,fixed)&&read(el)===fixed;
          el.dispatchEvent(new Event('input',{bubbles:true}));
        }
      }catch{/* Offer copy below; never print the exception or the message. */}
      if(!succeeded){fallback.value=fixed;fallback.hidden=false;copy.hidden=false;status.textContent='Could not update this editor. Copy fixed text and paste it yourself.';}
      else{fallback.value='';fallback.hidden=true;copy.hidden=true;status.textContent='Applied fixes. Review the current message before sending.';}
      refresh();show();
    }catch{status.textContent='Fix unavailable. Review and edit the message manually.';}
  }
  addButton('Fix all',()=>fix());
  const digest=async text=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text))),b=>b.toString(16).padStart(2,'0')).join('');
  const override=addButton('Send anyway',async()=>{
    const request=pending,el=composer();
    if(!request||!enabled||!el||read(el)!==request.text){pending=null;status.textContent='Message changed. Attempt send again to review the current message.';show();return;}
    override.disabled=true;
    try{
      const hash=await digest(request.text);
      if(pending!==request||read(el)!==request.text||!enabled)return;
      // Permit exists only during this synchronous replay and is consumed once.
      permit={hash,text:request.text};pending=null;
      try{
        if(request.kind==='click'){
          const button=sendButton();if(button&&!button.disabled)button.click();
          else status.textContent='Send button unavailable. Try sending again from the composer.';
        }else el.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',code:'Enter',bubbles:true,cancelable:true}));
      }finally{permit=null;}
      panel.hidden=true;badge.setAttribute('aria-expanded','false');list.replaceChildren();
      status.textContent='One send attempt permitted. If the site ignored it, use its send control and review again.';
    }catch{permit=null;status.textContent='Could not validate this send override. Sending remains blocked.';}
    finally{override.disabled=false;}
  });override.hidden=true;
  addButton('Close',hide);
  badge.onclick=()=>panel.hidden?show():hide();
  function intercept(event,kind){
    const el=composer();if(!enabled||!settingsReady||!el)return;
    const text=read(el);
    if(permit&&permit.text===text&&permit.hash){permit=null;return;}
    let findings;
    try{findings=detect(text);}catch{event.preventDefault();event.stopImmediatePropagation();status.textContent='Privacy check failed. Sending stopped.';show();return;}
    const counts=summarize(findings);if(!counts.block&&!counts.warn)return;
    event.preventDefault();event.stopImmediatePropagation();permit=null;pending={text,kind};show();override.focus();
  }
  document.addEventListener('keydown',event=>{
    if(event.key==='Enter'&&!event.shiftKey&&!event.isComposing&&composer()?.contains(event.target))intercept(event,'key');
  },true);
  document.addEventListener('click',event=>{
    const target=sendButton();if(target&&(event.target===target||target.contains(event.target)))intercept(event,'click');
  },true);
  document.addEventListener('input',event=>{
    if(composer()?.contains(event.target)){
      pending=null;permit=null;clearTimeout(timer);timer=setTimeout(()=>{refresh();if(!panel.hidden)show();},300);
    }
  },true);
  document.documentElement.append(host);
  const observer=new MutationObserver(records=>{
    if(records.some(r=>r.target!==host&&!host.contains(r.target))) {clearTimeout(timer);timer=setTimeout(refresh,300);}
  });observer.observe(document.body,{childList:true,subtree:true});
  const settingKey='enabled:'+location.hostname;
  chrome.storage.local.get({[settingKey]:true}).then(settings=>{enabled=settings[settingKey]===true;settingsReady=true;refresh();}).catch(()=>{badge.textContent='PrivacyGate inactive — settings unavailable';});
  chrome.storage.onChanged.addListener((changes,area)=>{if(area==='local'&&changes[settingKey]){enabled=changes[settingKey].newValue===true;hide();refresh();}});
})();
