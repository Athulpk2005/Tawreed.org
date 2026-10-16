/* Additive art direction. No authentication, forms, calculations or service copy replaced. */
(function () {
  'use strict';
  document.querySelectorAll('[data-art-hero]').forEach(function (hero) {
    var slides = Array.from(hero.querySelectorAll('[data-art-hero-slide]'));
    var dots = Array.from(hero.querySelectorAll('[data-art-hero-go]'));
    var labels = Array.from(hero.querySelectorAll('[data-art-hero-label]'));
    var current = 0;
    function show(next) {
      current = (next + slides.length) % slides.length;
      slides.forEach(function (slide, i) { slide.hidden = i !== current; });
      dots.forEach(function (dot, i) { dot.setAttribute('aria-current', String(i === current)); });
      labels.forEach(function (label, i) { label.hidden = i !== current; });
      hero.querySelector('[data-art-hero-status]').textContent = String(current + 1).padStart(2, '0') + ' / ' + String(slides.length).padStart(2, '0');
    }
    hero.querySelector('[data-art-hero-prev]').addEventListener('click', function () { show(current - 1); });
    hero.querySelector('[data-art-hero-next]').addEventListener('click', function () { show(current + 1); });
    dots.forEach(function (dot) { dot.addEventListener('click', function () { show(Number(dot.dataset.artHeroGo)); }); });
    hero.querySelector('.art-hero-controls').addEventListener('keydown', function (e) {
      if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') { e.preventDefault(); show(current + (e.key === 'ArrowRight' ? 1 : -1)); }
      else if (e.key === 'Home' || e.key === 'End') { e.preventDefault(); show(e.key === 'Home' ? 0 : slides.length - 1); }
    });
    var start = null;
    hero.addEventListener('touchstart', function (e) {
      if (!e.target.closest('a,button,input,select,textarea')) start = { x: e.changedTouches[0].clientX, y: e.changedTouches[0].clientY };
    }, { passive: true });
    hero.addEventListener('touchend', function (e) {
      if (!start) return;
      var dx = e.changedTouches[0].clientX - start.x, dy = e.changedTouches[0].clientY - start.y;
      if (Math.abs(dx) > 60 && Math.abs(dx) > Math.abs(dy) * 1.3) show(current + (dx < 0 ? 1 : -1));
      start = null;
    }, { passive: true });
    hero.querySelector('.art-hero-controls').hidden = false;
    show(0); // Manual only. No automatic movement or hidden reading deadline.
  });
  document.querySelectorAll('[data-art-gallery]').forEach(function (gallery) {
    var slides = Array.from(gallery.querySelectorAll('[data-visual-slide]'));
    var buttons = Array.from(gallery.querySelectorAll('[data-art-gallery-go]'));
    var next = gallery.querySelector('[data-visual-next]');
    function currentIndex() { return slides.findIndex(function (slide) { return !slide.hidden; }); }
    function update() { var active = currentIndex(); buttons.forEach(function (button, i) { button.setAttribute('aria-current', String(i === active)); }); }
    buttons.forEach(function (button) { button.addEventListener('click', function () {
      var target = Number(button.dataset.artGalleryGo);
      // Drive the established controls so their existing state remains authoritative.
      for (var i = 0; i < slides.length && currentIndex() !== target; i += 1) next.click();
      update();
    }); });
    new MutationObserver(update).observe(gallery, { subtree: true, attributes: true, attributeFilter: ['hidden'] });
    gallery.querySelector('.art-gallery-thumbs').hidden = false;
    update();
  });
})();
