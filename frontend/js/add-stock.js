/**
 * Smart Watchlist — Add Stock Modal Component
 */

class AddStockModal {
  constructor() {
    this.overlay = document.getElementById('add-stock-modal');
    this.closeBtn = document.getElementById('btn-close-modal');
    this.searchStep = document.getElementById('modal-step-search');
    this.thesisStep = document.getElementById('modal-step-thesis');

    this.searchInput = document.getElementById('modal-search-input');
    this.searchResults = document.getElementById('modal-search-results');
    this.searchSpinner = document.getElementById('search-spinner');

    this.selectedCompanyEl = document.getElementById('modal-selected-company');
    this.selectedSymbolEl = document.getElementById('modal-selected-symbol');
    this.thesisTextInput = document.getElementById('modal-thesis-text');
    this.btnAddConfirm = document.getElementById('btn-confirm-add-stock');
    this.btnBackToSearch = document.getElementById('btn-back-to-search');

    this.selectedStock = null;
    this.selectedCategory = 'Growth';
    this.debounceTimer = null;

    this.initEvents();
  }

  initEvents() {
    if (this.closeBtn) {
      this.closeBtn.addEventListener('click', () => this.close());
    }

    if (this.overlay) {
      this.overlay.addEventListener('click', (e) => {
        if (e.target === this.overlay) this.close();
      });
    }

    if (this.searchInput) {
      this.searchInput.addEventListener('input', (e) => {
        clearTimeout(this.debounceTimer);
        const query = e.target.value.trim();
        if (query.length >= 1) {
          this.debounceTimer = setTimeout(() => this.performSearch(query), 300);
        } else {
          this.searchResults.innerHTML = '';
          this.searchResults.classList.remove('show');
        }
      });
    }

    if (this.btnBackToSearch) {
      this.btnBackToSearch.addEventListener('click', () => {
        this.thesisStep.style.display = 'none';
        this.searchStep.style.display = 'block';
      });
    }

    // Category pills selection
    const catLabels = document.querySelectorAll('.cat-pill-label');
    catLabels.forEach(lbl => {
      lbl.addEventListener('click', () => {
        catLabels.forEach(l => l.classList.remove('selected'));
        lbl.classList.add('selected');
        const radio = lbl.querySelector('input[type="radio"]');
        if (radio) {
          radio.checked = true;
          this.selectedCategory = radio.value;
        }
      });
    });

    if (this.btnAddConfirm) {
      this.btnAddConfirm.addEventListener('click', () => this.submitStockAndThesis());
    }
  }

  open() {
    this.selectedStock = null;
    this.searchInput.value = '';
    this.searchResults.innerHTML = '';
    this.searchResults.classList.remove('show');
    this.thesisTextInput.value = '';
    this.searchStep.style.display = 'block';
    this.thesisStep.style.display = 'none';
    this.overlay.classList.add('open');
    setTimeout(() => this.searchInput.focus(), 100);
  }

  close() {
    this.overlay.classList.remove('open');
  }

  async performSearch(query) {
    if (this.searchSpinner) this.searchSpinner.style.display = 'inline-block';
    try {
      const results = await window.api.searchStocks(query);
      this.renderSearchResults(results);
    } catch (e) {
      console.error('Stock search error:', e);
      this.searchResults.innerHTML = `<div style="padding: 1rem; color: var(--text-muted); font-size: 0.85rem;">No matches found or provider unavailable.</div>`;
      this.searchResults.classList.add('show');
    } finally {
      if (this.searchSpinner) this.searchSpinner.style.display = 'none';
    }
  }

  renderSearchResults(results) {
    this.searchResults.innerHTML = '';
    if (!results || results.length === 0) {
      this.searchResults.innerHTML = `<div style="padding: 1rem; color: var(--text-muted); font-size: 0.85rem;">No matching companies found.</div>`;
      this.searchResults.classList.add('show');
      return;
    }

    results.forEach(stock => {
      const item = document.createElement('div');
      item.className = 'search-item';
      const cleanSym = stock.symbol.replace('.NS', '').replace('.BO', '');

      item.innerHTML = `
        <div>
          <div class="search-item-name">${this.escapeHtml(stock.name)}</div>
          <div class="search-item-meta">
            <span style="font-family: var(--font-mono); font-size: 0.75rem; color: var(--text-muted);">${cleanSym}</span>
            <span class="badge-freshness">${stock.exchange || 'NSE'}</span>
          </div>
        </div>
        <div style="font-size: 1.1rem; color: var(--brand-primary);">+</div>
      `;

      item.addEventListener('click', () => {
        this.selectStockForThesis(stock);
      });

      this.searchResults.appendChild(item);
    });

    this.searchResults.classList.add('show');
  }

  selectStockForThesis(stock) {
    this.selectedStock = stock;
    this.searchResults.classList.remove('show');
    this.searchStep.style.display = 'none';
    this.thesisStep.style.display = 'block';

    if (this.selectedCompanyEl) this.selectedCompanyEl.textContent = stock.name.toUpperCase();
    if (this.selectedSymbolEl) this.selectedSymbolEl.textContent = stock.symbol;

    // Set suggested placeholder based on company
    const sym = stock.symbol.toUpperCase();
    if (sym.includes('RELIANCE')) {
      this.thesisTextInput.placeholder = "e.g. I think Jio growth will continue and improve Reliance's performance.";
    } else if (sym.includes('TATA') || sym.includes('MOTORS')) {
      this.thesisTextInput.placeholder = "e.g. EV market share expansion and JLR margin recovery will strengthen earnings.";
    } else if (sym.includes('INFY') || sym.includes('TCS')) {
      this.thesisTextInput.placeholder = "e.g. I think IT demand will recover as discretionary enterprise spending resumes.";
    } else {
      this.thesisTextInput.placeholder = "e.g. I think operating margins will expand due to lower input costs and strong volume growth.";
    }

    setTimeout(() => this.thesisTextInput.focus(), 100);
  }

  async submitStockAndThesis() {
    if (!this.selectedStock) return;

    let thesisText = this.thesisTextInput.value.trim();
    if (!thesisText) {
      thesisText = `Watching ${this.selectedStock.name} based on ${this.selectedCategory} thesis.`;
    }

    this.btnAddConfirm.disabled = true;
    this.btnAddConfirm.textContent = 'Structuring Thesis & Evaluating...';

    try {
      const activeWl = window.appState.currentWatchlist || (await window.api.getWatchlists())[0];
      if (!activeWl) throw new Error('No active watchlist found.');

      await window.api.addStockToWatchlist(activeWl.id, {
        symbol: this.selectedStock.symbol,
        companyName: this.selectedStock.name,
        exchange: this.selectedStock.exchange || 'NSE',
        category: this.selectedCategory,
        thesisText: thesisText
      });

      this.close();
      // Navigate directly to the company page so user sees thesis immediately!
      window.appState.setView('company', { symbol: this.selectedStock.symbol });
    } catch (err) {
      console.error('Error adding stock with thesis:', err);
      alert(err.message || 'Failed to add stock.');
    } finally {
      this.btnAddConfirm.disabled = false;
      this.btnAddConfirm.textContent = 'Add to Watchlist';
    }
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

window.AddStockModal = AddStockModal;
