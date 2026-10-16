/* Tawreed ATS only. No dependency on, or modification to, the marketing scripts. */
'use strict';
window.TawreedATS = (() => {
  const root = 'api/ats/v1';
  let csrf = '', user = null;
  function el(tag, attrs = {}, children = []) {
    const node = document.createElement(tag);
    for (const [key, value] of Object.entries(attrs)) {
      if (value === null || value === undefined || value === false) continue;
      if (key === 'text') node.textContent = value;
      else if (key === 'class') node.className = value;
      else if (key.startsWith('on') && typeof value === 'function') node.addEventListener(key.slice(2), value);
      else if (['value','checked','disabled','hidden'].includes(key)) node[key] = value;
      else node.setAttribute(key, value === true ? '' : String(value));
    }
    for (const child of Array.isArray(children) ? children : [children]) if (child !== null && child !== undefined) node.append(child instanceof Node ? child : document.createTextNode(String(child)));
    return node;
  }
  async function api(path, options = {}) {
    if (location.protocol === 'file:') throw new Error('The job portal needs its application server. Start the Job Portal launcher, then open the local website URL.');
    const headers = {...options.headers};
    if (options.body && !(options.body instanceof FormData)) {headers['Content-Type']='application/json'; options.body=JSON.stringify(options.body);}
    if (options.method && options.method !== 'GET') headers['X-CSRF-Token']=csrf;
    let response;
    try {response=await fetch(root+path,{...options,headers,credentials:'same-origin',cache:'no-store'});}
    catch (_) {throw new Error('The recruitment service is unavailable. Please check the server connection and try again.');}
    let data;
    try {data=await response.json();} catch (_) {throw new Error('The recruitment service did not return a valid response. Please start the application server.');}
    if (!response.ok) {const error=new Error(data.error || 'The request could not be completed.');error.status=response.status;throw error;}
    if (data.csrf) csrf=data.csrf;
    if ('user' in data) user=data.user;
    return data;
  }
  async function session(){return api('/session');}
  function message(target,text,kind='error') {
    if(typeof target==='string') target=document.getElementById(target);
    if(target) target.replaceChildren(text ? el('div',{class:'ats-alert '+kind,text}) : document.createTextNode(''));
  }
  function select(target, options, firstLabel = null) {
    if(typeof target==='string')target=document.getElementById(target);
    const nodes=[];
    if(firstLabel !== null)nodes.push(el('option',{value:'',text:firstLabel}));
    for(const x of options)nodes.push(el('option',{value:typeof x==='object'?x.value:x,text:typeof x==='object'?x.label:x}));
    target.replaceChildren(...nodes);
  }
  function badge(value) {return el('span',{class:'ats-badge '+value.replace(/[^a-zA-Z]/g,''),text:value});}
  function when(value) {return value?new Date(value).toLocaleString(undefined,{dateStyle:'medium',timeStyle:'short'}):'—';}
  function money(value) {return value === null || value === undefined ? 'Not stated' : 'AED '+Number(value).toLocaleString(undefined,{maximumFractionDigits:2});}
  function salary(job) {return job.salary_min !== null && job.salary_max !== null ? money(job.salary_min)+' – '+money(job.salary_max).replace('AED ','')+' / month' : job.salary_min !== null ? 'From '+money(job.salary_min)+' / month' : job.salary_max !== null ? 'Up to '+money(job.salary_max)+' / month' : 'Discussed during selection';}
  async function busy(form, fn) {
    const buttons=[...form.querySelectorAll('[type=submit]')];buttons.forEach(b=>b.disabled=true);form.setAttribute('aria-busy','true');
    try{return await fn();}finally{buttons.forEach(b=>b.disabled=false);form.removeAttribute('aria-busy');}
  }
  document.querySelectorAll('[data-ats-password]').forEach(button=>button.addEventListener('click',()=>{const input=document.getElementById(button.dataset.atsPassword);const show=input.type==='password';input.type=show?'text':'password';button.textContent=show?'Hide':'Show';button.setAttribute('aria-label',show?'Hide password':'Show password');}));
  document.querySelectorAll('[data-ats-close]').forEach(b=>b.addEventListener('click',()=>b.closest('dialog').close()));
  return {api,session,el,message,select,badge,when,money,salary,busy,get user(){return user;}};
})();
