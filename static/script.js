(function(){
const chat = document.getElementById('chat');
const input = document.getElementById('userInput');
const send = document.getElementById('sendBtn');
const form = document.getElementById('composer');
const typing = document.getElementById('typing');
const toast = document.getElementById('toast');
const toggleTheme = document.getElementById('toggleTheme');
const clearBtn = document.getElementById('clearChatBtn');


// prefs
const prefs = JSON.parse(localStorage.getItem('bodai:prefs')||'{}');
if(prefs.theme){
  document.body.classList.remove('theme-light','theme-dark');
  document.body.classList.add(prefs.theme==='light'?'theme-light':'theme-dark');
}


// helpers
function el(tag, cls){ const e=document.createElement(tag); if(cls) e.className=cls; return e; }
function showToast(msg){ if(!toast) return; toast.textContent=msg; toast.classList.remove('hidden'); setTimeout(()=> toast.classList.add('hidden'), 1500); }
function scrollToEnd(){ chat.scrollTop = chat.scrollHeight; }
function avatar(content){ const a=el('div','avatar'); a.textContent=content; return a; }


function addMessage(text, sender){
  const wrap = el('div', 'message '+sender);
  if(sender==='bot') wrap.appendChild(avatar('🤖'));
  const bubble = el('div', 'bubble');
  bubble.textContent = text;
  if(sender==='user') bubble.setAttribute('data-you','');
  wrap.appendChild(bubble);
  if(sender==='user') wrap.appendChild(avatar('👤'));
  chat.appendChild(wrap);
  scrollToEnd();
}


function setTyping(on){ if(!typing) return; typing.classList.toggle('hidden', !on); }


async function sendMessage(text){
  if(!text) return;
  addMessage(text, 'user');
  setTyping(true);
  try{
    const resp = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text })
    });
    if (!resp.ok) throw new Error('Network response was not ok');
    const data = await resp.json();
    addMessage(data?.reply || '[Eroare: raspuns invalid]', 'bot');
  }catch(err){
    console.error(err);
    addMessage('[Eroare de retea]', 'bot');
  }finally{
    setTyping(false);
  }
}


// form submit
form?.addEventListener('submit', (e)=>{
  e.preventDefault();
  const text = (input?.value||'').trim();
  if(!text) return;
  input.value = '';
  sendMessage(text);
});


// theme toggle
toggleTheme?.addEventListener('click', ()=>{
  const isDark = document.body.classList.contains('theme-dark');
  const next = isDark ? 'theme-light' : 'theme-dark';
  document.body.classList.remove('theme-light','theme-dark');
  document.body.classList.add(next);
  const p = JSON.parse(localStorage.getItem('bodai:prefs')||'{}');
  p.theme = next === 'theme-light' ? 'light' : 'dark';
  localStorage.setItem('bodai:prefs', JSON.stringify(p));
});


// clear chat
clearBtn?.addEventListener('click', ()=>{
  chat.innerHTML = '';
  showToast('Chat curatat');
});


// greeting
const greeted = sessionStorage.getItem('bodai:greet');
if(!greeted){
  const name = (prefs.name||'').trim();
  addMessage(`Salut${name?`, ${name}`:''}! Eu sunt BODAI. Cu ce te pot ajuta astazi?`, 'bot');
  sessionStorage.setItem('bodai:greet','1');
}
})()