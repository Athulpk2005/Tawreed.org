'use strict';
(async()=>{
  const A=window.TawreedATS, $=id=>document.getElementById(id), page=document.querySelector('[data-ats-page]')?.dataset.atsPage;
  const empty=(title,body)=>A.el('div',{class:'ats-empty'},[A.el('img',{src:'assets/brand/tawreed-t-64.png',alt:'',width:45,height:45}),A.el('h2',{text:title}),A.el('p',{class:'ats-small',text:body})]);
  if(page==='jobs') {
    let currentPage=1,totalPages=1,sequence=0;
    async function load(){
      const seq=++sequence, params=new URLSearchParams(new FormData($('ats-filter-form')));params.set('page',currentPage);
      $('ats-jobs').setAttribute('aria-busy','true');A.message('ats-job-status','');
      try{
        const data=await A.api('/jobs?'+params);
        if(seq!==sequence)return;
        $('ats-results-count').textContent=data.total+' open '+(data.total===1?'vacancy':'vacancies');totalPages=data.pages;
        const cards=data.jobs.map(j=>A.el('article',{class:'ats-job'},[
          A.el('div',{class:'ats-topline'},[A.badge(j.employment_type),A.el('span',{class:'ats-small',text:j.reference})]),
          A.el('h2',{},[A.el('a',{href:'job-details.html?job='+encodeURIComponent(j.reference),text:j.title})]),
          A.el('div',{class:'ats-job-meta'},[A.el('span',{text:j.emirate}), ' · ', A.el('span',{text:j.sector})]),
          A.el('p',{text:j.summary}),A.el('p',{class:'ats-small',text:A.salary(j)}),
          A.el('div',{class:'ats-job-foot'},[A.el('span',{class:'ats-small',text:'Closes '+j.closing_date}),A.el('a',{class:'ats-subtle-link',href:'job-details.html?job='+encodeURIComponent(j.reference),text:'View role & apply →'})])
        ]));
        $('ats-jobs').replaceChildren(...(cards.length?cards:[empty('No matching vacancies right now.','Try another filter or return soon. We publish opportunities here once they have been approved and are open for applications.')]));
        $('ats-job-pagination').hidden=data.pages<2;$('ats-page-label').textContent='Page '+currentPage+' of '+data.pages;$('ats-prev').disabled=currentPage<=1;$('ats-next').disabled=currentPage>=data.pages;
      }catch(error){if(seq!==sequence)return;$('ats-jobs').replaceChildren(empty('Vacancies are temporarily unavailable.','Please try again later or contact info@tawreed.org for recruitment support.'));$('ats-results-count').textContent='Recruitment portal';A.message('ats-job-status',error.message);$('ats-job-pagination').hidden=true;}
      finally{if(seq===sequence)$('ats-jobs').setAttribute('aria-busy','false');}
    }
    $('ats-filter-form').addEventListener('submit',e=>{e.preventDefault();currentPage=1;load();});
    $('ats-filter-form').addEventListener('reset',()=>setTimeout(()=>{currentPage=1;load();},0));
    $('ats-prev').addEventListener('click',()=>{if(currentPage>1){currentPage--;load();}});
    $('ats-next').addEventListener('click',()=>{if(currentPage<totalPages){currentPage++;load();}});
    try{const o=await A.api('/options');A.select('ats-sector',o.sectors,'All expertise');A.select('ats-emirate',o.emirates,'All emirates');A.select('ats-employment_type',o.employment_types,'All types');}catch(e){A.message('ats-job-status',e.message);}
    await load();
  }
  if(page==='job-details'){
    const reference=new URLSearchParams(location.search).get('job');
    if(!reference){A.message('ats-detail-status','Choose an open vacancy from the job portal to view its details.');return;}
    try{
      const [data,o]=await Promise.all([A.api('/jobs/'+encodeURIComponent(reference)),A.api('/options'),A.session()]);
      const j=data.job;$('ats-job-title').textContent=j.title;document.title=j.title+' | Tawreed careers';
      $('ats-job-heading-meta').replaceChildren(A.badge(j.employment_type),A.badge(j.emirate),A.el('span',{class:'ats-small',text:j.reference}));
      for(const key of ['description','responsibilities','requirements','benefits'])$('ats-job-'+key).textContent=j[key];
      $('ats-benefits-section').hidden=!j.benefits;
      $('ats-job-facts').replaceChildren(...[['Location',j.location],['Expertise',j.sector],['Employment',j.employment_type],['Monthly salary',A.salary(j)],['Apply by',j.closing_date],['Reference',j.reference]].flatMap(([k,v])=>[A.el('div',{},[A.el('dt',{text:k}),A.el('dd',{text:v})])]));
      A.select('ats-visa_status',o.visa_statuses,'Select your status');$('ats-job-detail').hidden=false;
    }catch(error){A.message('ats-detail-status',error.message);return;}
    $('ats-application-form').addEventListener('submit',async event=>{
      event.preventDefault();const form=event.currentTarget,cv=$('ats-cv').files[0];
      if(!form.reportValidity())return;
      if(!cv || !/\.(pdf|docx)$/i.test(cv.name) || cv.size>8*1024*1024 || cv.size===0){A.message('ats-apply-status','Attach a non-empty PDF or DOCX CV no larger than 8 MB.');return;}
      await A.busy(form,async()=>{try{
        A.message('ats-apply-status','Uploading your application. Please keep this page open.','');
        const data=await A.api('/jobs/'+encodeURIComponent(reference)+'/applications',{method:'POST',body:new FormData(form)});
        $('ats-application-content').hidden=true;$('ats-receipt').hidden=false;
        $('ats-receipt').replaceChildren(A.el('h2',{text:'Application received.'}),A.el('p',{text:data.message}),A.el('code',{text:data.reference}),A.el('p',{class:'ats-small',text:'Save this reference for any follow-up with info@tawreed.org. No email receipt is sent by this portal.'}),A.el('a',{href:'jobs.html',class:'ats-btn',text:'Explore other vacancies →'}));
        form.reset();$('ats-receipt').focus();
      }catch(error){A.message('ats-apply-status',error.message);}});
    });
  }
})();
