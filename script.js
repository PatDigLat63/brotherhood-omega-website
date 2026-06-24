/* Brotherhood Omega Dynasty Empire — script.js */

(function () {
  'use strict';

  /* ===== Navbar: scroll class + mobile toggle ===== */
  var navbar = document.getElementById('navbar');
  var navToggle = document.getElementById('navToggle');
  var navLinks = document.getElementById('navLinks');

  window.addEventListener('scroll', function () {
    if (window.scrollY > 20) {
      navbar.classList.add('scrolled');
    } else {
      navbar.classList.remove('scrolled');
    }
  });

  if (navToggle && navLinks) {
    navToggle.addEventListener('click', function () {
      var isOpen = navLinks.classList.toggle('open');
      navToggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    });

    // Close menu when a link is clicked
    navLinks.querySelectorAll('a').forEach(function (link) {
      link.addEventListener('click', function () {
        navLinks.classList.remove('open');
        navToggle.setAttribute('aria-expanded', 'false');
      });
    });
  }

  /* ===== Scroll-reveal: add 'visible' class when elements enter viewport ===== */
  var revealTargets = document.querySelectorAll(
    '.agent-card, .pillar, .fortress-stat, .anthem-card, .team-card, .swarm-node'
  );

  if ('IntersectionObserver' in window) {
    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible');
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12 }
    );

    revealTargets.forEach(function (el) {
      el.classList.add('reveal');
      observer.observe(el);
    });
  }

  /* ===== Active nav link highlight on scroll ===== */
  var sections = document.querySelectorAll('section[id]');
  var navLinkEls = document.querySelectorAll('.nav-links a');

  function updateActiveNav() {
    var scrollPos = window.scrollY + 80;
    sections.forEach(function (section) {
      var top = section.offsetTop;
      var bottom = top + section.offsetHeight;
      var id = section.getAttribute('id');
      if (scrollPos >= top && scrollPos < bottom) {
        navLinkEls.forEach(function (link) {
          link.classList.remove('active');
          if (link.getAttribute('href') === '#' + id) {
            link.classList.add('active');
          }
        });
      }
    });
  }

  window.addEventListener('scroll', updateActiveNav, { passive: true });
  updateActiveNav();

  /* ===== Anthem play button interaction ===== */
  document.querySelectorAll('.anthem-play:not(.cs)').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var card = btn.closest('.anthem-card');
      var title = card.querySelector('h3') ? card.querySelector('h3').textContent : 'Anthem';
      // Visual feedback — pulse animation
      btn.style.transform = 'scale(0.9)';
      setTimeout(function () { btn.style.transform = ''; }, 150);
    });
  });

})();
