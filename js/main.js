/* Buildless, dependency-free interactions. Local previews never transmit form data or credentials. */
(function () {
  'use strict';
  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));
  const config = window.TAWREED_CONFIG || {};
  $$('[data-year]').forEach(el => { el.textContent = new Date().getFullYear(); });

  // Mobile navigation: retain peer-relative anchors as the non-JavaScript destination.
  const menu = $('#mobileNav');
  const menuToggle = $('[data-menu-toggle]');
  function closeMenu(returnFocus = false) {
    if (!menu || !menuToggle) return;
    menu.hidden = true;
    menuToggle.setAttribute('aria-expanded', 'false');
    menuToggle.setAttribute('aria-label', 'Open navigation');
    document.body.classList.remove('menu-open');
    if (returnFocus) menuToggle.focus();
  }
  if (menuToggle && menu) {
    menuToggle.addEventListener('click', () => {
      const opening = menu.hidden;
      menu.hidden = !opening;
      menuToggle.setAttribute('aria-expanded', String(opening));
      menuToggle.setAttribute('aria-label', opening ? 'Close navigation' : 'Open navigation');
      document.body.classList.toggle('menu-open', opening);
      if (opening) $('a', menu).focus();
    });
    $$('a', menu).forEach(a => a.addEventListener('click', () => closeMenu()));
    window.addEventListener('resize', () => { if (window.innerWidth > 980) closeMenu(); });
  }
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && menu && !menu.hidden) closeMenu(true);
    if (menu && !menu.hidden && event.key === 'Tab') {
      const links = $$('a', menu);
      if (!event.shiftKey && document.activeElement === links[links.length - 1]) { event.preventDefault(); menuToggle.focus(); }
      else if (event.shiftKey && document.activeElement === menuToggle) { event.preventDefault(); links[links.length - 1].focus(); }
    }
  });
  // Close desktop service menu after clicking outside or pressing Escape.
  const dropdown = $('.nav-dropdown');
  document.addEventListener('click', event => { if (dropdown && !dropdown.contains(event.target)) dropdown.open = false; });
  document.addEventListener('keydown', event => { if (event.key === 'Escape' && dropdown) dropdown.open = false; });

  // Native modal supplies focus trapping and Escape handling in supported browsers.
  const modal = $('#erpLoginModal');
  let portalOpener = null;
  $$('[data-portal-trigger]').forEach(anchor => anchor.addEventListener('click', event => {
    if (!modal || typeof modal.showModal !== 'function') return; // Normal fallback link remains usable.
    event.preventDefault();
    portalOpener = anchor;
    closeMenu();
    if (!modal.open) modal.showModal();
    document.body.classList.add('modal-open');
  }));
  if (modal) {
    $('[data-close-modal]', modal).addEventListener('click', () => modal.close());
    modal.addEventListener('click', event => { if (event.target === modal) { const r = modal.getBoundingClientRect(); if (event.clientX < r.left || event.clientX > r.right || event.clientY < r.top || event.clientY > r.bottom) modal.close(); } });
    modal.addEventListener('close', () => {
      document.body.classList.remove('modal-open');
      $$('[data-password]', modal).forEach(input => { input.value = ''; input.type = 'password'; });
      if (portalOpener && portalOpener.offsetParent !== null) portalOpener.focus();
      else if (menuToggle && menuToggle.offsetParent !== null) menuToggle.focus();
    });
  }

  // Integration boundary: replace this preview handler with the secure auth adapter.
  // AUTH requires HTTPS, POST, server-side rate limits, CSRF/origin protection,
  // role authorisation and HttpOnly Secure sessions. Never persist passwords locally.
  $$('[data-portal-widget]').forEach(widget => {
    const form = $('[data-portal-form]', widget);
    const status = $('[data-portal-status]', widget);
    const password = $('[data-password]', widget);
    const toggle = $('[data-password-toggle]', widget);
    const identity = $('[data-login-identity]', widget);
    const tabs = $$('[data-portal-role]', widget);
    $('[data-login-fields]', widget).disabled = false;
    let role = 'employee';
    const tell = message => { status.textContent = message; status.classList.remove('error'); };
    function selectRole(tab, focus = false) {
      role = tab.dataset.portalRole;
      tabs.forEach(item => { const active = item === tab; item.setAttribute('aria-selected', String(active)); item.tabIndex = active ? 0 : -1; });
      $('[role=tabpanel]', widget).setAttribute('aria-labelledby', tab.id);
      identity.placeholder = role === 'employee' ? 'TWD-EMP-00001' : 'Your work email';
      status.textContent = '';
      if (focus) tab.focus();
    }
    tabs.forEach((tab, index) => {
      tab.addEventListener('click', () => selectRole(tab));
      tab.addEventListener('keydown', event => {
        let target;
        if (event.key === 'ArrowRight') target = (index + 1) % tabs.length;
        if (event.key === 'ArrowLeft') target = (index + tabs.length - 1) % tabs.length;
        if (event.key === 'Home') target = 0;
        if (event.key === 'End') target = tabs.length - 1;
        if (target !== undefined) { event.preventDefault(); selectRole(tabs[target], true); }
      });
    });
    toggle.addEventListener('click', () => {
      const showing = password.type === 'password';
      password.type = showing ? 'text' : 'password';
      toggle.textContent = showing ? 'Hide' : 'Show';
      toggle.setAttribute('aria-label', showing ? 'Hide password' : 'Show password');
    });
    form.addEventListener('submit', event => {
      event.preventDefault();
      if (!form.reportValidity()) return;
      password.value = '';
      password.type = 'password';
      toggle.textContent = 'Show';
      toggle.setAttribute('aria-label', 'Show password');
      tell('Live sign-in is not enabled. No credentials were sent or stored. Please use your assigned account coordinator for access.');
      // ERP AUTH ENDPOINT HOOK: config.authEndpoint, POST {identity, password, role}.
      // Endpoint configuration alone does not enable authentication; implement the reviewed adapter.
    });
    $('[data-reset]', widget).addEventListener('click', () => tell('Password reset is not active in this preview. Contact your assigned account coordinator through your existing verified support channel.'));
    $$('[data-sso]', widget).forEach(button => button.addEventListener('click', () => tell((button.dataset.sso === 'uae' ? 'UAE PASS' : 'Microsoft 365') + ' single sign-on is not connected. No sign-in request has been sent.')));
  });

  // Illustrative calculator: finite numbers only, explicit scope, no claimed savings.
  const calculator = $('[data-calculator]');
  if (calculator) {
    const headcount = $('#headcount');
    const fee = $('#managementFee');
    const budget = $('#adminBudget');
    const money = value => 'AED ' + new Intl.NumberFormat('en-AE', { maximumFractionDigits: 2 }).format(value);
    function calculate() {
      const inputs = [headcount, fee, budget];
      if (inputs.some(input => input.value === '' || !input.validity.valid || !Number.isFinite(Number(input.value)))) {
        $('#calculatorStatus').textContent = 'Enter a valid fee and budget within the shown limits.';
        $('#monthlyFee').textContent = '—';
        $('#budgetVariance').textContent = '—';
        return;
      }
      $('#calculatorStatus').textContent = '';
      const count = Number(headcount.value), rate = Number(fee.value), total = count * rate;
      const difference = Number(budget.value) - total;
      $('#headcountValue').textContent = count + (count === 1 ? ' person' : ' people');
      $('#monthlyFee').textContent = money(total);
      $('#budgetVariance').textContent = money(Math.abs(difference));
      $('#varianceLabel').textContent = difference >= 0 ? 'Below your entered budget' : 'Above your entered budget';
      $('#calculatorDetail').textContent = count + (count === 1 ? ' person' : ' people') + ' × ' + money(rate) + ' per month';
    }
    calculator.addEventListener('input', calculate);
    calculator.addEventListener('submit', event => event.preventDefault());
    calculate();
  }

  // Manual carousel has no autoplay or moving-content time limit.
  const slides = $$('[data-slide]');
  if (slides.length) {
    let slide = 0;
    function showSlide(next) { slide = (next + slides.length) % slides.length; slides.forEach((el, i) => { el.hidden = i !== slide; }); $('[data-carousel-status]').textContent = (slide + 1) + ' of ' + slides.length; }
    $('[data-carousel-prev]').addEventListener('click', () => showSlide(slide - 1));
    $('[data-carousel-next]').addEventListener('click', () => showSlide(slide + 1));
  }

  // Multi-step RFP: browser validation + local JSON export + explicit email action.
  const rfp = $('[data-rfp-form]');
  if (rfp) {
    const steps = $$('[data-form-step]', rfp), indicators = $$('[data-step-indicator]', rfp);
    const back = $('[data-form-back]', rfp), next = $('[data-form-next]', rfp), submit = $('[data-form-submit]', rfp);
    const status = $('#rfpStatus'), files = $('#rfpDocuments');
    let step = 0, brief = null;
    const service = new URLSearchParams(location.search).get('service');
    if (['recruitment', 'headhunting', 'professional', 'industrial', 'eor', 'emiratisation', 'managed', 'corporate', 'it-erp', 'payroll', 'hospitality-fm', 'overseas', 'advisory'].includes(service)) $('#category').value = service;
    function syncServiceFields() {
      const selected = $('#category').value;
      const isCorporate = selected === 'corporate', isERP = selected === 'it-erp';
      const workforce = !isCorporate && !isERP && selected !== 'advisory';
      const headcount = $('#requiredHeadcount');
      $('[data-headcount-group]', rfp).hidden = !workforce;
      headcount.disabled = !workforce;
      headcount.required = workforce;
      [['[data-corporate-fields]', isCorporate], ['[data-erp-fields]', isERP]].forEach(([selector, active]) => {
        const group = $(selector, rfp); group.hidden = !active;
        $$('input,select', group).forEach(input => { input.disabled = !active; input.required = active && input.tagName === 'SELECT'; });
      });
      const isSearch = selected === 'recruitment' || selected === 'headhunting';
      $('#scope').placeholder = isCorporate
        ? 'Business activity, ownership or jurisdiction needs, registrations or approvals, target launch date and any certification requirements.'
        : isERP
          ? 'HR consultation priorities, current and target HRMS/ERP, modules, user groups, integrations, data scope and change-support needs.'
          : isSearch
            ? 'Position, role outcomes, essential skills, compensation range, target start date and any confidentiality requirements.'
            : 'Assignment duration, role mix, headcount, locations, shifts, readiness requirements and target start date.';
    }
    $('#category').addEventListener('change', syncServiceFields);
    syncServiceFields();
    function showStep(index, focus = true) {
      step = index;
      steps.forEach((item, i) => { item.hidden = i !== step; });
      indicators.forEach((item, i) => { item.classList.toggle('active', i <= step); if (i === step) item.setAttribute('aria-current', 'step'); else item.removeAttribute('aria-current'); });
      back.hidden = step === 0; next.hidden = step === steps.length - 1; submit.hidden = !next.hidden;
      status.textContent = '';
      if (focus) $('input,select,textarea', steps[step]).focus();
    }
    function validateStep() {
      for (const input of $$('input,select,textarea', steps[step])) {
        if (!input.checkValidity()) { input.reportValidity(); return false; }
      }
      return true;
    }
    next.addEventListener('click', () => { if (validateStep()) showStep(Math.min(step + 1, steps.length - 1)); });
    back.addEventListener('click', () => showStep(Math.max(step - 1, 0)));
    files.addEventListener('change', () => {
      const values = Array.from(files.files || []);
      const invalid = values.find(file => !/\.(pdf|doc|docx|xls|xlsx|txt)$/i.test(file.name) || file.size > 10 * 1024 * 1024);
      const message = values.length > 5 ? 'Choose no more than 5 files.' : invalid ? 'Each file must be PDF, Word, Excel or TXT and no larger than 10 MB.' : '';
      files.setCustomValidity(message);
      $('#fileStatus').textContent = message || (values.length ? values.length + ' file(s) selected. Nothing has been uploaded.' : '');
      $('#fileStatus').classList.toggle('error', Boolean(message));
    });
    function downloadBrief() {
      if (!brief) return;
      const blob = new Blob([JSON.stringify(brief, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob), anchor = document.createElement('a');
      anchor.href = url; anchor.download = 'Tawreed_RFP_Brief.json'; document.body.append(anchor); anchor.click(); anchor.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    }
    rfp.addEventListener('submit', event => {
      event.preventDefault();
      if (step < steps.length - 1) { if (validateStep()) showStep(step + 1); return; }
      // Validate every step again to cover programmatic or changed values.
      for (let i = 0; i < steps.length; i += 1) {
        const invalid = $$('input,select,textarea', steps[i]).find(input => !input.checkValidity());
        if (invalid) { showStep(i, false); invalid.reportValidity(); return; }
      }
      const data = Object.fromEntries(new FormData(rfp).entries()); delete data.documents;
      brief = { schemaVersion: '1.0', preparedAt: new Date().toISOString(), status: 'prepared-locally-not-submitted', company: config.legalName || 'Tawreed L.L.C.', requirement: data, attachments: Array.from(files.files || []).map(file => ({ name: file.name, bytes: file.size, type: file.type, contentIncluded: false })) };
      const summary = $('#rfpSummary'); summary.replaceChildren();
      const rows = [['Client', data.clientEntity], ['Contact', data.contactName + ' · ' + data.workEmail], ['Service', $('#category').selectedOptions[0].textContent]];
      if (data.headcount) rows.push(['Headcount', data.headcount]);
      if (data.businessJurisdiction) rows.push(['Business route', data.businessJurisdiction], ['Corporate scope', data.approvalScope]);
      if (data.erpScope) rows.push(['ERP scope', data.erpScope]);
      if (data.currentSystem) rows.push(['Current system', data.currentSystem]);
      if (data.targetSystem) rows.push(['Preferred system', data.targetSystem]);
      if (data.systemUsers) rows.push(['Users in scope', data.systemUsers]);
      rows.push(['Location', data.emirate], ['Timeline', data.urgency]);
      rows.forEach(([key, value]) => {
        const row = document.createElement('div'), dt = document.createElement('dt'), dd = document.createElement('dd');
        dt.textContent = key; dd.textContent = value; row.append(dt, dd); summary.append(row);
      });
      const subject = 'Tawreed service enquiry — ' + data.clientEntity;
      const body = ['Hello Tawreed,', '', 'Please review our service requirement:', ...rows.map(([key, value]) => key + ': ' + value), 'Reference: ' + (data.lpoReference || 'Not specified'), '', data.scope, '', 'I will attach the downloaded RFP brief and supporting documents separately.'].join('\n');
      $('#emailBrief').href = 'mailto:' + (config.email || 'info@tawreed.org') + '?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(body);
      rfp.hidden = true; $('#rfpResult').hidden = false; $('#rfpResult').focus();
    });
    $('#downloadBrief').addEventListener('click', downloadBrief);
    $('#editBrief').addEventListener('click', () => { $('#rfpResult').hidden = true; rfp.hidden = false; showStep(0); });
    showStep(0, false);
  }
})();

/* Eight-service image carousel: native touch scrolling, keyboard, responsive groups, wrap. */
(function () {
 'use strict';
 document.querySelectorAll('[data-service-carousel]').forEach(function (root) {
  const track=root.querySelector('[data-service-track]');
  const cards=Array.from(root.querySelectorAll('[data-service-card]'));
  const previous=root.querySelector('[data-service-prev]');
  const next=root.querySelector('[data-service-next]');
  const pagination=root.querySelector('[data-service-pagination]');
  const status=root.querySelector('[data-service-status]');
  if(!track||!cards.length||!previous||!next||!pagination||!status)return;
  let current=0,visible=1,max=cards.length-1,step=1,ticking=false,scrollTimer;
  const reduce=window.matchMedia('(prefers-reduced-motion: reduce)');
  function update(){
   status.textContent='Services '+String(current+1).padStart(2,'0')+'–'+String(Math.min(cards.length,current+visible)).padStart(2,'0')+' of '+String(cards.length).padStart(2,'0');
   Array.from(pagination.children).forEach(function(dot,i){dot.setAttribute('aria-current',String(i===current));});
  }
  function show(index,instant){
   current=index<0?max:index>max?0:index;
   update();
   track.scrollTo({left:current*step,behavior:instant||reduce.matches?'auto':'smooth'});
  }
  function measure(){
   visible=Math.max(1,Math.min(cards.length,parseInt(getComputedStyle(root).getPropertyValue('--service-visible'),10)||1));
   max=Math.max(0,cards.length-visible);
   step=cards[0].getBoundingClientRect().width+(parseFloat(getComputedStyle(track).columnGap)||24);
   current=Math.min(current,max);
   pagination.replaceChildren();
   for(let i=0;i<=max;i++){
    const dot=document.createElement('button');dot.type='button';dot.setAttribute('aria-label','Show services '+(i+1)+' to '+Math.min(cards.length,i+visible));
    dot.addEventListener('click',function(){show(i,false);});pagination.append(dot);
   }
   previous.hidden=max===0;next.hidden=max===0;show(current,true);
  }
  previous.addEventListener('click',function(){show(current-1,false);});
  next.addEventListener('click',function(){show(current+1,false);});
  track.addEventListener('keydown',function(event){
   if(event.target!==track)return;
   if(['ArrowRight','ArrowLeft','Home','End'].includes(event.key)){
    event.preventDefault();show(event.key==='Home'?0:event.key==='End'?max:current+(event.key==='ArrowRight'?1:-1),false);
   }
  });
  track.addEventListener('scroll',function(){
   clearTimeout(scrollTimer);
   scrollTimer=setTimeout(function(){current=Math.max(0,Math.min(max,Math.round(track.scrollLeft/step)));update();},100);
  },{passive:true});
  window.addEventListener('resize',function(){if(!ticking){ticking=true;requestAnimationFrame(function(){measure();ticking=false;});}});
  measure();
 });
})();
