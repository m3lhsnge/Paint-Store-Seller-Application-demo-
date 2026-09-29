// ─── PAGE MODULES ─────────────────────────────────────────────────────
// Her hash → { render: async fn, title, init?, roles?, navRoute? }
const routes = {};

function registerPage(hash, title, renderFn, opts = {}) {
  routes[hash] = {
    title,
    render: renderFn,
    init: opts.init || null,          // render sonrası çağrılır (window.__init_* yerine)
    roles: opts.roles || null,        // sadece bu roller erişebilir
    navRoute: opts.navRoute || hash,  // sidebar'da aktif gösterilecek menü
  };
}

// ─── ROUTER ───────────────────────────────────────────────────────────
const router = {
  current: null,

  async navigate(hash) {
    if (!hash || hash === '#') hash = '#dashboard';
    this.current = hash;

    const content = document.getElementById('page-content');
    const topbarTitle = document.getElementById('topbar-title');

    const route = routes[hash];
    if (!route) {
      content.innerHTML = `<div class="empty-state"><h3>Sayfa bulunamadı</h3><p>${esc(hash)}</p></div>`;
      return;
    }

    // Nav aktif state
    document.querySelectorAll('.nav-item').forEach(el => {
      el.classList.toggle('active', el.dataset.route === route.navRoute);
    });

    if (route.roles && !auth.hasRole(...route.roles)) {
      topbarTitle.textContent = route.title;
      content.innerHTML = `<div class="empty-state"><h3>Yetkiniz yok</h3><p>Bu sayfaya erişim izniniz bulunmuyor.</p></div>`;
      return;
    }

    topbarTitle.textContent = route.title;
    content.innerHTML = `<div class="loading-center"><span class="spinner"></span></div>`;

    try {
      const html = await route.render();
      content.innerHTML = html;
      // Sayfa mount sonrası init
      if (route.init) {
        route.init();
      } else if (window[`__init_${hash.replace('#','')}`]) {
        window[`__init_${hash.replace('#','')}`]();
      }
    } catch (e) {
      content.innerHTML = `<div class="empty-state"><h3>Hata</h3><p>${esc(e.message)}</p></div>`;
    }
  },

  // Aktif sayfayı yeniden yükler (hash değişmediği için hashchange tetiklenmez)
  refresh() {
    return this.navigate(this.current || location.hash || '#dashboard');
  },

  init() {
    window.addEventListener('hashchange', () => this.navigate(location.hash));
    this.navigate(location.hash || '#dashboard');
  }
};
