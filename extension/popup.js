(async()=>{
 const status=document.getElementById('status');
 for(const site of ['chatgpt.com','claude.ai','gemini.google.com']){
  const key='enabled:'+site,label=document.createElement('label'),input=document.createElement('input');input.type='checkbox';input.disabled=true;
  label.append(input,document.createTextNode(' '+site));document.getElementById('settings').append(label);
  try{const settings=await chrome.storage.local.get({[key]:true});input.checked=settings[key]===true;input.disabled=false;}
  catch{status.textContent='Settings unavailable.';}
  input.onchange=async()=>{try{await chrome.storage.local.set({[key]:input.checked});status.textContent='Setting saved.';}catch{status.textContent='Could not save setting.';}};
 }
})();
