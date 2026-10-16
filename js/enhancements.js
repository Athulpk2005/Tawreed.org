/* Accessible content layers and progressive imagery. No authentication or data transport. */
(function () {
  'use strict';
  // Keep complete local previews useful without caching or downloading remote photographs.
  document.querySelectorAll('img[data-offline-src]').forEach(function (image) {
    function fallback() {
      if (image.dataset.fallbackUsed) return;
      image.dataset.fallbackUsed = 'true';
      image.dataset.photographAlt = image.alt;
      image.alt = 'Illustrative architectural artwork; the online version uses the sourced photograph.';
      image.loading = 'eager';
      image.src = image.dataset.offlineSrc;
    }
    image.addEventListener('error', fallback);
    if (location.protocol === 'file:') image.loading = 'eager';
    if (!navigator.onLine || (image.complete && !image.naturalWidth)) fallback();
  });
  document.querySelectorAll('[data-content-tabs]').forEach(function (group) {
    const nav = group.querySelector('[role="tablist"]');
    const tabs = Array.from(group.querySelectorAll('[data-content-tab]'));
    const panels = Array.from(group.querySelectorAll('[data-content-panel]'));
    if (!nav || tabs.length !== panels.length) return;
    function activate(index, focus) {
      tabs.forEach(function (tab, i) {
        const active = i === index;
        tab.setAttribute('aria-selected', String(active));
        tab.tabIndex = active ? 0 : -1;
        panels[i].hidden = !active;
      });
      if (focus) tabs[index].focus();
    }
    nav.hidden = false;
    tabs.forEach(function (tab, index) {
      tab.addEventListener('click', function () { activate(index, false); });
      tab.addEventListener('keydown', function (event) {
        let target;
        if (event.key === 'ArrowRight') target = (index + 1) % tabs.length;
        if (event.key === 'ArrowLeft') target = (index + tabs.length - 1) % tabs.length;
        if (event.key === 'Home') target = 0;
        if (event.key === 'End') target = tabs.length - 1;
        if (target !== undefined) { event.preventDefault(); activate(target, true); }
      });
    });
    activate(0, false);
  });
  // Each carousel is independent, manual and keyboard operable. No autoplay.
  document.querySelectorAll('[data-visual-carousel]').forEach(function (carousel) {
    const slides = Array.from(carousel.querySelectorAll('[data-visual-slide]'));
    const controls = carousel.querySelector('[data-visual-controls]');
    const previous = carousel.querySelector('[data-visual-prev]');
    const next = carousel.querySelector('[data-visual-next]');
    const status = carousel.querySelector('[data-visual-status]');
    if (!slides.length || !controls || !previous || !next || !status) return;
    let current = 0;
    function show(index) {
      current = (index + slides.length) % slides.length;
      slides.forEach(function (slide, i) { slide.hidden = i !== current; });
      status.textContent = (current + 1) + ' / ' + slides.length;
    }
    controls.hidden = false;
    previous.addEventListener('click', function () { show(current - 1); });
    next.addEventListener('click', function () { show(current + 1); });
    controls.addEventListener('keydown', function (event) {
      if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
        event.preventDefault(); show(current + (event.key === 'ArrowRight' ? 1 : -1));
      }
    });
    show(0);
  });
})();
