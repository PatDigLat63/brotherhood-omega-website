/* Brotherhood Omega Dynasty Empire — script.js */

(function () {
  'use strict';

  const REVEAL_THRESHOLD = 0.12;
  const CONTACT_EMAIL = 'contact@brotherhoodomega.com';

  /* ===== Set contact email link ===== */
  const contactBtn = document.querySelector('.contact-btn');
  if (contactBtn) {
    contactBtn.href = 'mailto:' + CONTACT_EMAIL;
  }

  /* ===== Navbar: scroll class + mobile toggle ===== */
  const navbar = document.getElementById('navbar');
  const navToggle = document.getElementById('navToggle');
  const navLinks = document.getElementById('navLinks');

  window.addEventListener('scroll', function () {
    if (window.scrollY > 20) {
      navbar.classList.add('scrolled');
    } else {
      navbar.classList.remove('scrolled');
    }
  });

  if (navToggle && navLinks) {
    navToggle.addEventListener('click', function () {
      const isOpen = navLinks.classList.toggle('open');
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
  const revealTargets = document.querySelectorAll(
    '.agent-card, .pillar, .fortress-stat, .anthem-card, .team-card, .swarm-node'
  );

  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible');
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: REVEAL_THRESHOLD }
    );

    revealTargets.forEach(function (el) {
      el.classList.add('reveal');
      observer.observe(el);
    });
  }

  /* ===== Active nav link highlight on scroll ===== */
  const sections = document.querySelectorAll('section[id]');
  const navLinkEls = document.querySelectorAll('.nav-links a');

  function updateActiveNav() {
    const scrollPos = window.scrollY + 80;
    sections.forEach(function (section) {
      const top = section.offsetTop;
      const bottom = top + section.offsetHeight;
      const id = section.getAttribute('id');
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
      // Visual feedback — pulse animation
      btn.style.transform = 'scale(0.9)';
      setTimeout(function () { btn.style.transform = ''; }, 150);
    });
  });

})();
