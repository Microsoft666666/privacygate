"""User-gesture clipboard with honest fallback. Receives only validated text."""
import streamlit as st

_clipboard = st.components.v2.component('privacygate_copy', html='''<button type="button">Copy to clipboard</button><p role="status" aria-live="polite"></p><textarea aria-label="Approved text for manual copy" readonly hidden></textarea>''', css='''button{background:#14161a;color:white;border:0;border-radius:12px;padding:12px 20px;font:500 15px system-ui;min-height:44px;cursor:pointer}button:focus-visible{outline:3px solid #1d5c4e;outline-offset:3px}p,textarea{font:14px system-ui;color:#454b54}textarea{width:95%;height:120px}''', js='''export default function({data,parentElement}) {
 const button=parentElement.querySelector('button');
 const status=parentElement.querySelector('p');
 const fallback=parentElement.querySelector('textarea');
 button.onclick=async()=>{
   // Prevent copying an earlier validated snapshot while editors have pending changes.
   const editors=[...document.querySelectorAll('textarea')];
   const changed=editors.some(e=>(e.getAttribute('aria-label')==='Edit the revised text' && e.value!==data.text) || (e.getAttribute('aria-label')==='Your message' && e.value!==data.source));
   if(changed){status.textContent='Message changed. Review it again before copying.';return;}
   try {await navigator.clipboard.writeText(data.text);status.textContent='Copied reviewed message';}
   catch {status.textContent='Clipboard unavailable. Select and copy the approved text below.';fallback.hidden=false;fallback.value=data.text;fallback.focus();fallback.select();}
 };
 return ()=>{button.onclick=null;};
}''')

def render_copy(text, fingerprint):
    st.caption('Draft validated. Use the button below to allow browser clipboard access.')
    _clipboard(key='clipboard_'+fingerprint, data={'text': text, 'source': st.session_state.source})
