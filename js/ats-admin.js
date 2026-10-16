'use strict';
(async()=>{
  const A=window.TawreedATS,$=id=>document.getElementById(id),page=document.querySelector('[data-ats-page]')?.dataset.atsPage;
  const button=(text,fn,kind='')=>A.el('button',{type:'button',class:'ats-btn small '+kind,text,onclick:async e=>{const b=e.currentTarget;b.disabled=true;try{await fn();}catch(error){A.message('ats-workspace-status',error.message);}finally{b.disabled=false;}}});
  function table(headers,rows,empty='No records to display.'){
    if(!rows.length)return A.el('div',{class:'ats-empty'},[A.el('p',{text:empty})]);
    return A.el('div',{class:'ats-table-wrap'},[A.el('table',{class:'ats-table'},[A.el('thead',{},[A.el('tr',{},headers.map(t=>A.el('th',{scope:'col',text:t})))]),A.el('tbody',{},rows.map(cells=>A.el('tr',{},cells.map(c=>A.el('td',{},c)))))])]);
  }
  let options,jobs=[],users=[],editing=null,userReset=null,appPage=1,appPages=1,candidateId=null;
  function view(tab){
    document.querySelectorAll('[data-ats-tab]').forEach(b=>b.setAttribute('aria-current',String(b.dataset.atsTab===tab)));
    for(const s of document.querySelectorAll('.ats-tabsection'))s.hidden=s.id!=='ats-tab-'+tab;
    if(tab==='applications')loadApplications().catch(err=>A.message('ats-workspace-status',err.message));
    if(tab==='team')loadUsers().catch(err=>A.message('ats-workspace-status',err.message));
    if(tab==='audit')loadAudit().catch(err=>A.message('ats-workspace-status',err.message));
  }
  async function actJob(j,action){
    let note='';
    if(action==='return'){note=prompt('What should the recruiter amend?');if(!note)return;}
    if(action==='close'&&!confirm('Close this vacancy? It will stop accepting new applications. Existing applications remain available.'))return;
    await A.api('/staff/jobs/'+j.id+'/transition',{method:'POST',body:{action,note}});A.message('ats-workspace-status',action==='approve'?'Vacancy approved and published.':'Vacancy workflow updated.','success');await loadJobs();
  }
  function renderJobs(){
    const selected=$('ats-staff-job-status').value;
    const filtered=jobs.filter(j=>selected==='All statuses'||j.status===selected);
    $('ats-stat-grid').replaceChildren(...[['Total vacancies',jobs.length],['Awaiting approval',jobs.filter(j=>j.status==='pending').length],['Published',jobs.filter(j=>j.status==='published'&&j.closing_date>=new Date().toLocaleDateString('en-CA')).length],['Applications',jobs.reduce((n,j)=>n+j.application_count,0)]].map(([k,v])=>A.el('div',{class:'ats-stat'},[A.el('b',{text:v}),A.el('span',{text:k})])));
    $('ats-vacancies-table').replaceChildren(table(['Vacancy','Publication','Applications','Actions'],filtered.map(j=>{
      const actions=[button('Edit',()=>editJob(j))];
      if(['draft','closed'].includes(j.status))actions.push(button('Submit for approval',()=>actJob(j,'submit')));
      if(j.status==='pending'&&A.user.role==='admin')actions.push(button('Approve & publish',()=>actJob(j,'approve'),'primary'),button('Return',()=>actJob(j,'return')));
      if(j.status!=='closed')actions.push(button('Close',()=>actJob(j,'close')));
      if(j.status==='published')actions.push(A.el('a',{href:'job-details.html?job='+encodeURIComponent(j.reference),class:'ats-btn small',text:'Public view'}));
      return [[A.el('strong',{text:j.title}),A.el('small',{text:j.reference+' · '+j.emirate}),A.el('small',{text:'Owner: '+j.owner_name}),...(j.review_note?[A.el('small',{text:'Review: '+j.review_note})]:[])],[A.badge(j.status),A.el('small',{text:'Closes '+j.closing_date})],button(String(j.application_count)+' candidates',()=>{$('ats-candidate-job').value=j.id;appPage=1;view('applications');}),A.el('div',{class:'ats-inline'},actions)];
    }),'No vacancies in this view. Create a vacancy to start the approval workflow.'));
  }
  async function loadJobs(){
    jobs=(await A.api('/staff/jobs')).jobs;
    const selected=$('ats-candidate-job').value;A.select('ats-candidate-job',jobs.map(j=>({value:j.id,label:j.reference+' · '+j.title})),'All assigned vacancies');$('ats-candidate-job').value=selected;
    renderJobs();
  }
  async function editJob(j=null){
    editing=j;$('ats-job-editor').reset();A.message('ats-editor-status','');$('ats-job-dialog-title').textContent=j?'Edit vacancy · '+j.reference:'Create vacancy';
    if(A.user.role==='admin'){
      if(!users.length)await loadUsers();A.select('ats-owner_id',users.filter(u=>u.active).map(u=>({value:u.id,label:u.name+' · '+u.role})));$('ats-owner-field').hidden=false;$('ats-owner_id').value=j?j.owner_id:A.user.id;
    }
    if(j){for(const key of ['title','location','closing_date','salary_min','salary_max','summary','description','responsibilities','requirements','benefits'])$('ats-'+key).value=j[key]??'';for(const key of ['sector','emirate','employment_type'])$('ats-'+key+'-edit').value=j[key];}
    $('ats-job-dialog').showModal();
  }
  async function loadApplications(){
    const p=new URLSearchParams({page:appPage});const q=$('ats-candidate-query').value.trim(),job=$('ats-candidate-job').value,stage=$('ats-candidate-stage').value;
    if(q)p.set('q',q);if(job)p.set('job_id',job);if(stage)p.set('stage',stage);
    const data=await A.api('/staff/applications?'+p);appPages=data.pages;
    $('ats-app-count').textContent=data.total+' matching applications';
    $('ats-applications-table').replaceChildren(table(['Candidate','Vacancy','Stage','Received','Review'],data.applications.map(a=>[[A.el('strong',{text:a.full_name}),A.el('small',{text:a.email}),A.el('small',{text:a.reference})],[A.el('strong',{text:a.job_title}),A.el('small',{text:a.job_reference})],A.badge(a.stage),A.when(a.created_at),button('Open profile',()=>openCandidate(a.id))]),'No applications match the selected filters.'));
    $('ats-app-pagination').hidden=data.pages<2;$('ats-app-page').textContent='Page '+appPage+' of '+data.pages;$('ats-app-prev').disabled=appPage<=1;$('ats-app-next').disabled=appPage>=data.pages;
  }
  async function openCandidate(id){
    candidateId=id;const d=await A.api('/staff/applications/'+id),a=d.application;const body=$('ats-candidate-body');$('ats-candidate-title').textContent=a.full_name;
    const facts=A.el('dl',{class:'ats-facts ats-grid'},[['Reference',a.reference],['Vacancy',a.job_reference+' · '+a.job_title],['Email',a.email],['Telephone',a.phone],['Current location',a.current_location],['UAE status',a.visa_status],['Visa expiry',a.visa_expiry||'Not provided'],['Current monthly salary',A.money(a.current_salary)],['Expected monthly salary',A.money(a.expected_salary)],['Notice',a.notice_days+' days'],['Experience',a.experience_years+' years'],['Submitted',A.when(a.created_at)],['Privacy consent',A.when(a.consent_at)+' · v'+a.privacy_version]].map(([k,v])=>A.el('div',{},[A.el('dt',{text:k}),A.el('dd',{text:v})])));
    const status=A.el('div',{id:'ats-candidate-status',role:'status','aria-live':'polite'});
    const transition=A.el('form',{id:'ats-stage-form',method:'post'},[A.el('h3',{text:'Move through the pipeline'}),A.el('label',{for:'ats-next-stage',text:'Next stage'}),A.el('select',{id:'ats-next-stage',name:'stage',required:true}),A.el('label',{for:'ats-stage-note',text:'Decision note (optional)',style:'margin-top:15px'}),A.el('textarea',{id:'ats-stage-note',name:'note',maxlength:3000}),A.el('button',{class:'ats-btn primary',type:'submit',style:'margin-top:15px',text:'Update stage'})]);
    const noteForm=A.el('form',{method:'post',style:'margin-top:28px'},[A.el('h3',{text:'Private recruiter notes'}),A.el('label',{for:'ats-private-note',text:'Add a note'}),A.el('textarea',{id:'ats-private-note',name:'note',required:true,maxlength:4000}),A.el('button',{class:'ats-btn',type:'submit',style:'margin-top:12px',text:'Save note'})]);
    const notes=A.el('div',{},d.notes.map(n=>A.el('div',{class:'ats-note'},[A.el('strong',{class:'ats-small',text:n.actor+' · '+A.when(n.created_at)}),A.el('p',{text:n.note})])));
    const history=A.el('ol',{class:'ats-timeline'},d.history.map(h=>A.el('li',{},[A.el('strong',{text:(h.from_stage?h.from_stage+' → ':'')+h.to_stage}),A.el('p',{class:'ats-small',text:A.when(h.created_at)+' · '+(h.actor||'Candidate')}),...(h.note?[A.el('p',{text:h.note})]:[])])));
    body.replaceChildren(A.el('div',{class:'ats-toolbar'},[A.badge(a.stage),A.el('a',{class:'ats-btn primary',href:'api/ats/v1/staff/applications/'+id+'/cv',text:'Download CV ↓'})]),facts,...(a.cover_note?[A.el('h3',{style:'margin-top:25px',text:'Candidate note'}),A.el('p',{class:'ats-prose',text:a.cover_note})]:[]),A.el('p',{class:'ats-small',text:'CV: '+a.cv_name+' · '+(a.cv_scan==='clamav-passed'?'Security scan passed.':'Local development: antivirus scan is not configured. Scan files before opening.')}),A.el('hr',{style:'margin:25px 0;border:0;border-top:1px solid #E2E8F0'}),status);
    if(a.allowed_stages.length){body.append(transition);A.select('ats-next-stage',a.allowed_stages,'Choose next stage');transition.addEventListener('submit',async e=>{e.preventDefault();await A.busy(transition,async()=>{try{await A.api('/staff/applications/'+id+'/stage',{method:'POST',body:Object.fromEntries(new FormData(transition))});await openCandidate(id);await loadApplications();}catch(error){A.message(status,error.message);}});});}
    else body.append(A.el('p',{class:'ats-small',text:'This application has reached a terminal stage. The recorded history remains available.'}));
    body.append(noteForm,notes,A.el('h3',{style:'margin-top:30px',text:'Pipeline history'}),history);
    noteForm.addEventListener('submit',async e=>{e.preventDefault();await A.busy(noteForm,async()=>{try{await A.api('/staff/applications/'+id+'/notes',{method:'POST',body:Object.fromEntries(new FormData(noteForm))});await openCandidate(id);}catch(error){A.message(status,error.message);}});});
    if(A.user.role==='admin')body.append(A.el('div',{class:'ats-bottom-note'},[button('Delete application & CV',async()=>{if(!confirm('Permanently delete this candidate application, private notes, stage history and CV? This cannot be undone.'))return;await A.api('/staff/applications/'+id,{method:'DELETE'});$('ats-candidate-dialog').close();await loadApplications();await loadJobs();},'danger')]));
    if(!$('ats-candidate-dialog').open)$('ats-candidate-dialog').showModal();
  }
  async function loadUsers(){
    users=(await A.api('/staff/users')).users;
    $('ats-users-table').replaceChildren(table(['Account','Role','Access','Manage'],users.map(u=>[[A.el('strong',{text:u.name}),A.el('small',{text:u.email})],A.badge(u.role),[A.badge(u.active?'Active':'Disabled'),...(u.must_change?[A.el('small',{text:'Password change required'})]:[])],A.el('div',{class:'ats-inline'},[button(u.active?'Disable':'Enable',async()=>{if(!confirm((u.active?'Disable':'Enable')+' access for '+u.name+'? Existing sessions will be signed out.'))return;await A.api('/staff/users/'+u.id,{method:'PATCH',body:{active:!u.active}});if(u.id===A.user.id){location.href='recruiter-login.html';return;}await loadUsers();}),button('Reset password',()=>editUser(u)),button(u.role==='admin'?'Make recruiter':'Make admin',async()=>{if(!confirm('Change the access role for '+u.name+'?'))return;await A.api('/staff/users/'+u.id,{method:'PATCH',body:{role:u.role==='admin'?'recruiter':'admin'}});if(u.id===A.user.id){location.href='recruiter-login.html';return;}await loadUsers();})])])));
  }
  function editUser(user=null){
    userReset=user;$('ats-user-form').reset();A.message('ats-user-status','');$('ats-user-dialog-title').textContent=user?'Reset password · '+user.name:'Create team account';
    for(const key of ['user-name','user-email','user-role']){const node=$('ats-'+key);node.closest('.ats-field').hidden=!!user;node.disabled=!!user;}
    $('ats-user-dialog').showModal();
  }
  async function loadAudit(){const data=await A.api('/staff/audit');$('ats-audit-table').replaceChildren(table(['Time','Actor','Event','Record / detail'],data.events.map(e=>[A.when(e.created_at),e.actor||'System / candidate',e.action,[A.el('strong',{text:e.target}),A.el('small',{text:e.details})]])));}
  try{
    const s=await A.session();
    if(page==='recruiter-login'){
      if(s.user){location.replace('recruiter.html');return;}
      $('ats-login-form').addEventListener('submit',async e=>{e.preventDefault();const form=e.currentTarget;await A.busy(form,async()=>{try{await A.api('/login',{method:'POST',body:{email:$('ats-login-email').value,password:$('ats-login-password').value}});form.reset();location.href='recruiter.html';}catch(error){A.message('ats-login-status',error.message);}});});return;
    }
    if(page!=='recruiter')return;
    if(!s.user){location.replace('recruiter-login.html');return;}
    $('ats-workspace-loading').hidden=true;$('ats-workspace').hidden=false;$('ats-session-name').textContent=s.user.name;$('ats-session-role').textContent=s.user.role==='admin'?'Administrator':'Recruiter';
    const mustChange=!!s.user.must_change;
    document.querySelectorAll('[data-ats-tab]').forEach(b=>{b.hidden=mustChange?b.dataset.atsTab!=='account':b.hasAttribute('data-admin-only')&&s.user.role!=='admin';b.addEventListener('click',()=>view(b.dataset.atsTab));});
    $('ats-logout').addEventListener('click',async()=>{try{await A.api('/logout',{method:'POST'});}finally{location.href='recruiter-login.html';}});
    $('ats-password-form').addEventListener('submit',async e=>{e.preventDefault();const form=e.currentTarget;if($('ats-new_password').value!==$('ats-confirm_password').value){A.message('ats-password-status','New passwords do not match.');return;}await A.busy(form,async()=>{try{await A.api('/password',{method:'POST',body:{current_password:$('ats-current_password').value,new_password:$('ats-new_password').value}});form.reset();location.reload();}catch(error){A.message('ats-password-status',error.message);}});});
    if(mustChange){view('account');A.message('ats-workspace-status','Change your temporary password to activate your recruitment access.','');return;}
    options=await A.api('/options');A.select('ats-sector-edit',options.sectors,'Select expertise');A.select('ats-emirate-edit',options.emirates,'Select emirate');A.select('ats-employment_type-edit',options.employment_types,'Select employment type');A.select('ats-candidate-stage',options.stages,'All stages');
    $('ats-new-job').addEventListener('click',()=>editJob().catch(e=>A.message('ats-workspace-status',e.message)));
    $('ats-staff-job-status').addEventListener('change',renderJobs);
    $('ats-job-editor').addEventListener('submit',async e=>{e.preventDefault();const form=e.currentTarget;await A.busy(form,async()=>{try{const d=Object.fromEntries(new FormData(form));for(const key of ['sector','emirate','employment_type']){d[key]=d[key+'-edit'];delete d[key+'-edit'];}if(editing)d.version=editing.version;await A.api('/staff/jobs'+(editing?'/'+editing.id:''),{method:editing?'PUT':'POST',body:d});$('ats-job-dialog').close();A.message('ats-workspace-status','Draft saved. Submit it for administrator approval when ready.','success');await loadJobs();}catch(error){A.message('ats-editor-status',error.message);}});});
    $('ats-app-filters').addEventListener('submit',e=>{e.preventDefault();appPage=1;loadApplications().catch(e=>A.message('ats-workspace-status',e.message));});
    $('ats-refresh-apps').addEventListener('click',()=>loadApplications().catch(e=>A.message('ats-workspace-status',e.message)));
    $('ats-app-prev').addEventListener('click',()=>{if(appPage>1){appPage--;loadApplications().catch(e=>A.message('ats-workspace-status',e.message));}});
    $('ats-app-next').addEventListener('click',()=>{if(appPage<appPages){appPage++;loadApplications().catch(e=>A.message('ats-workspace-status',e.message));}});
    $('ats-new-user').addEventListener('click',()=>editUser());
    $('ats-user-form').addEventListener('submit',async e=>{e.preventDefault();const form=e.currentTarget;await A.busy(form,async()=>{try{const body=userReset?{password:$('ats-user-password').value}:{name:$('ats-user-name').value,email:$('ats-user-email').value,role:$('ats-user-role').value,password:$('ats-user-password').value};await A.api('/staff/users'+(userReset?'/'+userReset.id+'/reset-password':''),{method:'POST',body});form.reset();$('ats-user-dialog').close();await loadUsers();A.message('ats-workspace-status',userReset?'Temporary password replaced. Share it using your approved secure channel.':'Team account created. Share the temporary password using your approved secure channel.','success');}catch(error){A.message('ats-user-status',error.message);}});});
    $('ats-refresh-audit').addEventListener('click',()=>loadAudit().catch(e=>A.message('ats-workspace-status',e.message)));
    await loadJobs();
  }catch(error){
    if(page==='recruiter-login')A.message('ats-login-status',error.message);
    else{$('ats-workspace-loading').hidden=true;$('ats-workspace').hidden=false;view('account');A.message('ats-workspace-status',error.message);}
  }
})();
