// Shared site behavior: nav, mobile menu, smooth scroll, scroll reveal
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', e => {
    const target = document.querySelector(a.getAttribute('href'));
    if (target) {
      e.preventDefault();
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    const mm = document.getElementById('mobileMenu');
    if (mm && mm.classList.contains('open')) {
      mm.classList.remove('open');
      document.getElementById('navBurger').setAttribute('aria-expanded', 'false');
    }
  });
});

const nav = document.getElementById('siteNav');
window.addEventListener('scroll', () => {
  nav.classList.toggle('scrolled', window.scrollY > 20);
}, { passive: true });

const burger = document.getElementById('navBurger');
const mobileMenu = document.getElementById('mobileMenu');
burger.addEventListener('click', () => {
  const open = mobileMenu.classList.toggle('open');
  burger.setAttribute('aria-expanded', open ? 'true' : 'false');
});

const revealEls = document.querySelectorAll('.rv:not(.on)');
if ('IntersectionObserver' in window) {
  const ro = new IntersectionObserver((entries) => {
    entries.forEach(en => {
      if (en.isIntersecting) { en.target.classList.add('on'); ro.unobserve(en.target); }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
  revealEls.forEach(el => ro.observe(el));
} else {
  revealEls.forEach(el => el.classList.add('on'));
}
