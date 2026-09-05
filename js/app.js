/**
 * Thesis Watchlist — Main Application Orchestrator
 */

document.addEventListener('DOMContentLoaded', () => {
  // Initialize View Controllers
  window.homeView = new window.HomeView();
  window.watchlistView = new window.WatchlistView();
  window.addStockModal = new window.AddStockModal();
  window.companyView = new window.CompanyView();
  window.changesView = new window.ChangesView();

  const views = {
    home: document.getElementById('home-view'),
    watchlist: document.getElementById('watchlist-view'),
    company: document.getElementById('company-view'),
    changes: document.getElementById('changes-view')
  };

  // View Switcher Handler
  window.appState.on('viewChange', ({ view, params }) => {
    // Hide all views
    Object.values(views).forEach(v => {
      if (v) v.classList.remove('active');
    });

    // Show target view
    const targetViewEl = views[view];
    if (targetViewEl) {
      targetViewEl.classList.add('active');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // Update URL hash for clean navigation history
    let newHash = `#/${view}`;
    if (params && params.symbol) {
      newHash += `/${encodeURIComponent(params.symbol)}`;
    }
    if (window.location.hash !== newHash) {
      history.pushState(null, '', newHash);
    }

    // Load data for view
    if (view === 'home') {
      window.homeView.loadSummary();
    } else if (view === 'watchlist') {
      window.watchlistView.loadWatchlist();
    } else if (view === 'company' && params.symbol) {
      window.companyView.loadCompany(params.symbol);
    } else if (view === 'changes' && params.symbol) {
      window.changesView.loadWhatChanged(params.symbol);
    }
  });

  // Handle browser back/forward button navigation
  window.addEventListener('popstate', () => {
    routeFromHash();
  });

  function routeFromHash() {
    const hash = window.location.hash || '#/home';
    const parts = hash.replace('#/', '').split('/');
    const viewName = parts[0] || 'home';
    const symbol = parts[1] ? decodeURIComponent(parts[1]) : null;

    if (views[viewName]) {
      window.appState.setView(viewName, { symbol });
    } else {
      window.appState.setView('home');
    }
  }

  // Header Brand click goes to Home / Summary view
  const navBrand = document.querySelector('.nav-brand');
  if (navBrand) {
    navBrand.addEventListener('click', (e) => {
      e.preventDefault();
      window.appState.setView('home');
    });
  }

  // Initialize Real-Time WebSocket
  window.appState.initWebSocket();

  // Initial Route Check
  routeFromHash();
});
