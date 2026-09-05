/**
 * Thesis Watchlist — My Watchlist View Component
 */

class WatchlistView {
  constructor() {
    this.container = document.getElementById('watchlist-view');
    this.listContainer = document.getElementById('watchlist-items-list');
    this.searchInput = document.getElementById('watchlist-filter-input');
    this.btnAddStock = document.getElementById('btn-open-add-stock');
    this.btnRefreshAll = document.getElementById('btn-refresh-evaluations');
    this.rawItems = [];

    this.initEvents();
  }

  initEvents() {
    if (this.btnAddStock) {
      this.btnAddStock.addEventListener('click', () => {
        if (window.addStockModal) {
          window.addStockModal.open();
        }
      });
    }

    if (this.btnRefreshAll) {
      this.btnRefreshAll.addEventListener('click', async () => {
        this.btnRefreshAll.classList.add('loading');
        this.btnRefreshAll.textContent = 'Evaluating...';
        try {
          await window.api.runAllEvaluations();
          await this.loadWatchlist();
        } catch (e) {
          console.error('Error refreshing evaluations:', e);
        } finally {
          this.btnRefreshAll.classList.remove('loading');
          this.btnRefreshAll.innerHTML = '<span class="icon">🔄</span> Re-evaluate Signals';
        }
      });
    }

    if (this.searchInput) {
      this.searchInput.addEventListener('input', (e) => {
        this.filterItems(e.target.value);
      });
    }

    // Subscribe to WebSocket live quote updates
    window.appState.on('stockQuoteUpdated', ({ symbol, quoteData }) => {
      this.updateSingleItemDOM(symbol, quoteData);
    });
  }

  async loadWatchlist() {
    if (!this.listContainer) return;

    this.listContainer.innerHTML = `
      <div class="empty-state">
        <div class="spinner"></div>
        <div style="margin-top: 1rem; font-weight: 500;">Fetching live market quotes & evaluations...</div>
      </div>
    `;

    try {
      const watchlists = await window.api.getWatchlists();
      if (watchlists && watchlists.length > 0) {
        const activeWl = watchlists[0];
        window.appState.currentWatchlist = activeWl;
        this.rawItems = activeWl.items || [];
        this.renderItems(this.rawItems);

        // Subscribe to real-time quotes via WebSocket
        const symbolsToSubscribe = this.rawItems.map(i => i.symbol);
        if (symbolsToSubscribe.length > 0) {
          window.appState.subscribeSymbols(symbolsToSubscribe);
        }
      } else {
        this.renderEmptyState();
      }
    } catch (err) {
      console.error('Failed to load watchlist items:', err);
      this.listContainer.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-title">Error Loading Watchlist</div>
          <div style="color: #ef4444; margin-top: 0.5rem;">${err.message || 'Could not connect to backend server.'}</div>
        </div>
      `;
    }
  }

  filterItems(query) {
    const q = query.trim().toLowerCase();
    if (!q) {
      this.renderItems(this.rawItems);
      return;
    }
    const filtered = this.rawItems.filter(item => {
      return (item.companyName || '').toLowerCase().includes(q) ||
             (item.symbol || '').toLowerCase().includes(q) ||
             (item.thesisText || '').toLowerCase().includes(q);
    });
    this.renderItems(filtered);
  }

  renderItems(items) {
    if (!items || items.length === 0) {
      this.renderEmptyState();
      return;
    }

    this.listContainer.innerHTML = '';
    items.forEach(item => {
      const card = this.createStockCard(item);
      this.listContainer.appendChild(card);
    });
  }

  createStockCard(item) {
    const card = document.createElement('div');
    card.className = 'stock-card';
    card.setAttribute('data-symbol', item.symbol);

    const priceFormatted = (item.price !== null && item.price !== undefined && item.price > 0)
      ? `${item.currency || '₹'}${item.price.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
      : 'Loading...';

    const pct = item.percentageChange || 0;
    const isPositive = pct > 0;
    const isNegative = pct < 0;
    const changeClass = isPositive ? 'positive' : (isNegative ? 'negative' : 'neutral');
    const changeSign = isPositive ? '+' : '';
    const changeFormatted = `${changeSign}${pct.toFixed(2)}%`;

    // Status format (incorporating normal meaningful-change + thesis layer)
    let statusPill = '';
    const st = item.thesisStatus || 'NO_MEANINGFUL_CHANGE';
    if (st === 'THESIS_NEEDS_ATTENTION' || st === 'NEEDS_ATTENTION') {
      statusPill = `<span class="status-pill attention"><span class="status-dot attention"></span> 🟠 Thesis needs attention</span>`;
    } else if (st === 'THESIS_STRENGTHENING' || st === 'STRENGTHENING') {
      statusPill = `<span class="status-pill strengthening"><span class="status-dot strengthening"></span> 🟢 Meaningful change / thesis strengthening</span>`;
    } else if (st === 'MEANINGFUL_CHANGE' || item.hasMeaningfulChange) {
      statusPill = `<span class="status-pill meaningful"><span class="status-dot meaningful"></span> 🔵 Meaningful change</span>`;
    } else {
      statusPill = `<span class="status-pill nochange"><span class="status-dot nochange"></span> ⚪ No meaningful change</span>`;
    }

    const cleanSymbol = item.symbol.replace('.NS', '').replace('.BO', '');

    card.innerHTML = `
      <div class="stock-info-main">
        <div class="stock-company-name">${this.escapeHtml(item.companyName)}</div>
        <div class="stock-symbol-row">
          <span class="stock-symbol">${cleanSymbol}</span>
          <span class="badge-freshness ${item.freshness && item.freshness.includes('LIVE') ? 'live' : 'delayed'}">${item.freshness || 'DELAYED'}</span>
        </div>
        <div style="margin-top: 0.6rem;">
          ${statusPill}
        </div>
      </div>
      <div class="stock-price-col">
        <div class="stock-price price-val">${priceFormatted}</div>
        <div class="stock-change ${changeClass} change-val">${changeFormatted}</div>
        <button class="btn-remove-stock" type="button" title="Remove ${cleanSymbol} from watchlist" aria-label="Remove ${cleanSymbol} from watchlist">
          Remove
        </button>
      </div>
    `;

    // Handle stock deletion cleanly without page reload
    const removeBtn = card.querySelector('.btn-remove-stock');
    if (removeBtn) {
      removeBtn.addEventListener('click', async (e) => {
        e.stopPropagation(); // Do not trigger card navigation
        const confirmed = window.confirm(`Remove ${item.companyName} (${cleanSymbol}) from your watchlist?`);
        if (!confirmed) return;

        removeBtn.disabled = true;
        removeBtn.textContent = 'Removing...';

        try {
          const activeWl = window.appState.currentWatchlist;
          const wlId = activeWl ? activeWl.id : 'default';
          await window.api.deleteStockFromWatchlist(wlId, item.symbol);

          // Smoothly animate and remove card from DOM
          card.style.transition = 'all 0.25s ease-out';
          card.style.opacity = '0';
          card.style.transform = 'scale(0.96)';
          setTimeout(() => {
            card.remove();
            this.rawItems = this.rawItems.filter(i => i.symbol !== item.symbol);
            if (this.rawItems.length === 0) {
              this.renderEmptyState();
            }
          }, 250);
        } catch (err) {
          console.error('Failed to remove stock:', err);
          alert(`Could not remove stock: ${err.message || 'Server error'}`);
          removeBtn.disabled = false;
          removeBtn.textContent = 'Remove';
        }
      });
    }

    card.addEventListener('click', () => {
      window.appState.setView('company', { symbol: item.symbol });
    });

    return card;
  }

  updateSingleItemDOM(symbol, quoteData) {
    const card = this.listContainer.querySelector(`[data-symbol="${symbol}"]`);
    if (!card) return;

    const priceEl = card.querySelector('.price-val');
    const changeEl = card.querySelector('.change-val');

    if (priceEl && quoteData.price) {
      priceEl.textContent = `${quoteData.currency || '₹'}${quoteData.price.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }
    if (changeEl && quoteData.percentageChange !== undefined) {
      const pct = quoteData.percentageChange;
      const isPositive = pct > 0;
      const isNegative = pct < 0;
      changeEl.className = `stock-change ${isPositive ? 'positive' : (isNegative ? 'negative' : 'neutral')} change-val`;
      changeEl.textContent = `${isPositive ? '+' : ''}${pct.toFixed(2)}%`;
    }
  }

  renderEmptyState() {
    this.listContainer.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">📋</div>
        <div class="empty-state-title">Your Watchlist is Empty</div>
        <div style="margin-bottom: 1.5rem;">Add a real stock and specify your thesis to begin monitoring intelligence.</div>
        <button class="btn btn-primary" onclick="window.addStockModal.open()">+ Add Your First Stock</button>
      </div>
    `;
  }

  escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>'"]/g, tag => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      "'": '&#39;',
      '"': '&quot;'
    }[tag] || tag));
  }
}

window.WatchlistView = WatchlistView;
