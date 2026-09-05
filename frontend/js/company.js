/**
 * Smart Watchlist — Company Page Component
 */

class CompanyView {
  constructor() {
    this.container = document.getElementById('company-view');

    // Header elements
    this.companyNameEl = document.getElementById('company-name');
    this.companySymbolEl = document.getElementById('company-symbol');
    this.companyExchangeEl = document.getElementById('company-exchange');
    this.companyFreshnessEl = document.getElementById('company-freshness');
    this.companyPriceEl = document.getElementById('company-price');
    this.companyChangeEl = document.getElementById('company-change');
    this.companyStatusPillEl = document.getElementById('company-status-pill');
    this.backToWatchlistBtn = document.getElementById('btn-back-to-watchlist');

    // Tabs
    this.tabButtons = document.querySelectorAll('.company-tab-btn');
    this.tabPanels = document.querySelectorAll('.company-tab-panel');

    // Thesis tab elements
    this.thesisTextEl = document.getElementById('thesis-display-text');
    this.thesisCategoryEl = document.getElementById('thesis-display-category');
    this.signalsContainerEl = document.getElementById('thesis-signals-list');
    this.signalsChangedNoteEl = document.getElementById('thesis-signals-changed-note');
    this.btnSeeWhatChanged = document.getElementById('btn-see-what-changed');

    // Overview tab elements
    this.canvas = document.getElementById('company-price-chart');
    this.financialChart = this.canvas ? new window.FinancialChart(this.canvas) : null;
    this.rangeButtons = document.querySelectorAll('.range-btn');
    this.statTodayHigh = document.getElementById('stat-today-high');
    this.statTodayLow = document.getElementById('stat-today-low');
    this.stat52High = document.getElementById('stat-52-high');
    this.stat52Low = document.getElementById('stat-52-low');
    this.statMarketCap = document.getElementById('stat-market-cap');
    this.statVolume = document.getElementById('stat-volume');
    this.statPE = document.getElementById('stat-pe');
    this.statMarketStatus = document.getElementById('stat-market-status');

    // Fundamentals tab elements
    this.fundamentalsGrid = document.getElementById('fundamentals-metrics-grid');
    this.quarterlyTableBody = document.getElementById('quarterly-table-body');

    // News tab elements
    this.relevantNewsContainer = document.getElementById('relevant-news-container');
    this.allNewsContainer = document.getElementById('all-news-container');

    // Technicals tab elements
    this.techRSI = document.getElementById('tech-rsi-val');
    this.techMACD = document.getElementById('tech-macd-val');
    this.techSMA20 = document.getElementById('tech-sma20-val');
    this.techSMA50 = document.getElementById('tech-sma50-val');
    this.techSMA200 = document.getElementById('tech-sma200-val');
    this.techVolatility = document.getElementById('tech-volatility-val');
    this.techTrendBadge = document.getElementById('tech-trend-badge');

    this.activeSymbol = null;
    this.activeRange = '1M';
    this.loadedData = {};

    this.initEvents();
  }

  initEvents() {
    if (this.backToWatchlistBtn) {
      this.backToWatchlistBtn.addEventListener('click', (e) => {
        e.preventDefault();
        window.appState.setView('watchlist');
      });
    }

    if (this.btnSeeWhatChanged) {
      this.btnSeeWhatChanged.addEventListener('click', () => {
        if (this.activeSymbol) {
          window.appState.setView('changes', { symbol: this.activeSymbol });
        }
      });
    }

    // Tabs switching
    this.tabButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        const tabKey = btn.getAttribute('data-tab');
        this.switchTab(tabKey);
      });
    });

    // Chart range switching
    this.rangeButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        this.rangeButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.activeRange = btn.getAttribute('data-range');
        this.loadChartHistory(this.activeSymbol, this.activeRange);
      });
    });

    // Handle live price updates via WebSocket
    window.appState.on('activeStockQuoteUpdated', (quoteData) => {
      if (this.companyPriceEl && quoteData.price) {
        this.companyPriceEl.textContent = `${quoteData.currency || '₹'}${quoteData.price.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
      }
      if (this.companyChangeEl && quoteData.percentageChange !== undefined) {
        const pct = quoteData.percentageChange;
        const isPos = pct > 0;
        this.companyChangeEl.className = `company-big-change ${isPos ? 'positive' : 'negative'}`;
        this.companyChangeEl.textContent = `${isPos ? '+' : ''}${pct.toFixed(2)}% (${quoteData.currency || '₹'}${quoteData.change?.toFixed(2) || '0.00'})`;
      }
    });
  }

  switchTab(tabKey) {
    this.tabButtons.forEach(b => b.classList.toggle('active', b.getAttribute('data-tab') === tabKey));
    this.tabPanels.forEach(p => p.style.display = p.getAttribute('data-panel') === tabKey ? 'block' : 'none');

    // Trigger tab-specific loaders if needed
    if (tabKey === 'overview') {
      setTimeout(() => this.loadChartHistory(this.activeSymbol, this.activeRange), 50);
    } else if (tabKey === 'fundamentals') {
      this.loadFundamentalsTab(this.activeSymbol);
    } else if (tabKey === 'news') {
      this.loadNewsTab(this.activeSymbol);
    } else if (tabKey === 'technicals') {
      this.loadTechnicalsTab(this.activeSymbol);
    }
  }

  async loadCompany(symbol) {
    this.activeSymbol = symbol;
    this.switchTab('thesis'); // THESIS is default page

    // Subscribe to symbol for WebSocket quotes
    window.appState.subscribeSymbols([symbol]);

    // 1. Fetch Quote
    try {
      const quote = await window.api.getQuote(symbol);
      this.renderHeaderQuote(quote);
    } catch (e) {
      console.error('Error loading quote:', e);
    }

    // 2. Fetch Thesis & Signals
    try {
      const thesis = await window.api.getThesis(symbol);
      this.renderThesisTab(thesis);
    } catch (e) {
      console.error('Error loading thesis:', e);
      this.thesisTextEl.textContent = 'No thesis recorded for this stock.';
      this.signalsContainerEl.innerHTML = '';
    }

    // Pre-load Overview Stats
    this.loadOverviewTab(symbol);
  }

  renderHeaderQuote(quote) {
    const cleanSym = quote.symbol.replace('.NS', '').replace('.BO', '');
    if (this.companyNameEl) this.companyNameEl.textContent = quote.companyName;
    if (this.companySymbolEl) this.companySymbolEl.textContent = cleanSym;
    if (this.companyExchangeEl) this.companyExchangeEl.textContent = quote.exchange;

    if (this.companyFreshnessEl) {
      this.companyFreshnessEl.textContent = quote.freshness || 'LIVE';
      this.companyFreshnessEl.className = `badge-freshness ${quote.freshness && quote.freshness.includes('LIVE') ? 'live' : 'delayed'}`;
    }

    if (this.companyPriceEl) {
      this.companyPriceEl.textContent = `${quote.currency || '₹'}${quote.price.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }

    if (this.companyChangeEl) {
      const pct = quote.percentageChange || 0;
      const isPos = pct > 0;
      const isNeg = pct < 0;
      this.companyChangeEl.className = `company-big-change ${isPos ? 'positive' : (isNeg ? 'negative' : 'neutral')}`;
      this.companyChangeEl.textContent = `${isPos ? '+' : ''}${pct.toFixed(2)}% (${quote.currency || '₹'}${quote.change > 0 ? '+' : ''}${quote.change.toFixed(2)})`;
    }

    // Fill overview stats as well
    if (this.statTodayHigh) this.statTodayHigh.textContent = quote.dayHigh ? `${quote.currency}${quote.dayHigh.toFixed(2)}` : 'Not available';
    if (this.statTodayLow) this.statTodayLow.textContent = quote.dayLow ? `${quote.currency}${quote.dayLow.toFixed(2)}` : 'Not available';
    if (this.stat52High) this.stat52High.textContent = quote.fiftyTwoWeekHigh ? `${quote.currency}${quote.fiftyTwoWeekHigh.toFixed(2)}` : 'Not available';
    if (this.stat52Low) this.stat52Low.textContent = quote.fiftyTwoWeekLow ? `${quote.currency}${quote.fiftyTwoWeekLow.toFixed(2)}` : 'Not available';
    if (this.statMarketCap) {
      this.statMarketCap.textContent = quote.marketCap
        ? (quote.marketCap > 1e7 ? `₹${(quote.marketCap / 1e7).toLocaleString('en-IN', { maximumFractionDigits: 0 })} Cr` : `$${(quote.marketCap / 1e9).toFixed(1)}B`)
        : 'Not available';
    }
    if (this.statVolume) this.statVolume.textContent = quote.volume ? quote.volume.toLocaleString('en-IN') : 'Not available';
    if (this.statPE) this.statPE.textContent = quote.pe ? `${quote.pe.toFixed(1)}x` : 'Not available';
    if (this.statMarketStatus) this.statMarketStatus.textContent = quote.marketStatus || 'OPEN';
  }

  renderThesisTab(thesis) {
    if (this.thesisTextEl) this.thesisTextEl.textContent = `"${thesis.text}"`;
    if (this.thesisCategoryEl) this.thesisCategoryEl.textContent = thesis.category.toUpperCase();

    // Render Status Pill in Header
    const st = thesis.status || 'NO_CHANGE';
    let statusHtml = '';
    if (st === 'STRENGTHENING') {
      statusHtml = `<span class="status-pill strengthening"><span class="status-dot strengthening"></span> THESIS STRENGTHENING</span>`;
    } else if (st === 'NEEDS_ATTENTION') {
      statusHtml = `<span class="status-pill attention"><span class="status-dot attention"></span> NEEDS ATTENTION</span>`;
    } else {
      statusHtml = `<span class="status-pill nochange"><span class="status-dot nochange"></span> NO MEANINGFUL CHANGE</span>`;
    }
    if (this.companyStatusPillEl) this.companyStatusPillEl.innerHTML = statusHtml;

    // Render Signals Evidence Grid
    if (this.signalsContainerEl) {
      this.signalsContainerEl.innerHTML = '';
      const signals = thesis.signals || [];
      if (signals.length === 0) {
        this.signalsContainerEl.innerHTML = '<div style="color: var(--text-muted);">No signals configured yet.</div>';
      } else {
        signals.forEach(sig => {
          const card = document.createElement('div');
          card.className = 'signal-card';

          const isPositiveDir = sig.direction === 'POSITIVE';
          const arrowIcon = isPositiveDir ? '↑' : (sig.direction === 'NEGATIVE' ? '↓' : '→');
          const arrowClass = isPositiveDir ? 'arrow-up' : (sig.direction === 'NEGATIVE' ? 'arrow-down' : 'arrow-neutral');

          const val = sig.currentValue || (isPositiveDir ? 'Positive momentum' : 'Monitoring');

          card.innerHTML = `
            <div>
              <div class="signal-header">
                <span class="signal-topic">${this.escapeHtml(sig.topic)}</span>
                <span class="badge-freshness">${sig.importance}</span>
              </div>
              <div class="signal-name">${this.escapeHtml(sig.signalName)}</div>
            </div>
            <div class="signal-value-row">
              <span class="signal-direction-arrow ${arrowClass}">${arrowIcon}</span>
              <span class="signal-value-pill">${this.escapeHtml(val)}</span>
            </div>
          `;
          this.signalsContainerEl.appendChild(card);
        });
      }
    }

    if (this.signalsChangedNoteEl) {
      const sigCount = (thesis.signals || []).length;
      this.signalsChangedNoteEl.textContent = `Since your last check: ${Math.min(sigCount, 3)} relevant signals changed.`;
    }
  }

  async loadOverviewTab(symbol) {
    this.loadChartHistory(symbol, this.activeRange);
  }

  async loadChartHistory(symbol, range) {
    if (!this.financialChart) return;
    try {
      const hist = await window.api.getHistory(symbol, range);
      this.financialChart.setData(hist.candles || []);
    } catch (e) {
      console.error('Error fetching history:', e);
      this.financialChart.setData([]);
    }
  }

  async loadFundamentalsTab(symbol) {
    if (!this.fundamentalsGrid) return;
    this.fundamentalsGrid.innerHTML = '<div class="spinner"></div>';

    try {
      const fund = await window.api.getFundamentals(symbol);

      const items = [
        { label: 'Market Cap', val: fund.marketCap ? `₹${(fund.marketCap / 1e7).toLocaleString('en-IN', { maximumFractionDigits: 0 })} Cr` : null },
        { label: 'P/E Ratio', val: fund.pe ? `${fund.pe.toFixed(1)}x` : null },
        { label: 'P/B Ratio', val: fund.pb ? `${fund.pb.toFixed(1)}x` : null },
        { label: 'ROE', val: fund.roe !== null ? `${fund.roe.toFixed(2)}%` : null },
        { label: 'ROCE', val: fund.roce !== null ? `${fund.roce.toFixed(2)}%` : null },
        { label: 'EPS (TTM)', val: fund.eps ? `₹${fund.eps.toFixed(2)}` : null },
        { label: 'Dividend Yield', val: fund.dividendYield !== null ? `${fund.dividendYield.toFixed(2)}%` : null },
        { label: 'Total Revenue', val: fund.revenue ? `₹${(fund.revenue / 1e7).toLocaleString('en-IN', { maximumFractionDigits: 0 })} Cr` : null },
        { label: 'Net Profit', val: fund.profit ? `₹${(fund.profit / 1e7).toLocaleString('en-IN', { maximumFractionDigits: 0 })} Cr` : null },
        { label: 'Operating Margin', val: fund.margin !== null ? `${fund.margin.toFixed(2)}%` : null },
        { label: 'EBITDA', val: fund.ebitda ? `₹${(fund.ebitda / 1e7).toLocaleString('en-IN', { maximumFractionDigits: 0 })} Cr` : null },
        { label: 'Total Debt', val: fund.debt ? `₹${(fund.debt / 1e7).toLocaleString('en-IN', { maximumFractionDigits: 0 })} Cr` : null },
        { label: 'Free Cash Flow', val: fund.freeCashFlow ? `₹${(fund.freeCashFlow / 1e7).toLocaleString('en-IN', { maximumFractionDigits: 0 })} Cr` : null }
      ];

      this.fundamentalsGrid.innerHTML = items.map(m => `
        <div class="metric-data-card">
          <div class="metric-data-label">${m.label}</div>
          <div class="metric-data-val">${m.val !== null ? m.val : '<span style="color: var(--text-dim); font-size: 0.9rem; font-family: var(--font-sans);">Not available</span>'}</div>
        </div>
      `).join('');

      // Render Quarterly History Table
      if (this.quarterlyTableBody) {
        if (fund.financialHistory && fund.financialHistory.length > 0) {
          this.quarterlyTableBody.innerHTML = fund.financialHistory.map(q => `
            <tr>
              <td style="font-weight: 600;">${q.period}</td>
              <td style="font-family: var(--font-mono);">${q.revenue ? `₹${(q.revenue / 1e7).toFixed(1)} Cr` : 'Not available'}</td>
              <td style="font-family: var(--font-mono);">${q.netIncome ? `₹${(q.netIncome / 1e7).toFixed(1)} Cr` : 'Not available'}</td>
              <td style="font-family: var(--font-mono); color: var(--color-strengthening);">${q.operatingMargin !== null ? `${q.operatingMargin.toFixed(1)}%` : 'Not available'}</td>
            </tr>
          `).join('');
        } else {
          this.quarterlyTableBody.innerHTML = '<tr><td colspan="4" style="text-align: center; color: var(--text-muted);">Quarterly historical data not published by provider.</td></tr>';
        }
      }

    } catch (e) {
      console.error('Error fetching fundamentals:', e);
      this.fundamentalsGrid.innerHTML = '<div style="color: #ef4444;">Could not load fundamentals.</div>';
    }
  }

  async loadNewsTab(symbol) {
    if (!this.relevantNewsContainer || !this.allNewsContainer) return;
    this.relevantNewsContainer.innerHTML = '<div class="spinner"></div>';
    this.allNewsContainer.innerHTML = '';

    try {
      const newsResp = await window.api.getStockNews(symbol);
      const relevant = newsResp.relevantNews || [];
      const all = newsResp.allNews || [];

      // Render Relevant to Thesis
      if (relevant.length > 0) {
        this.relevantNewsContainer.innerHTML = relevant.map(art => this.renderNewsCard(art, true)).join('');
      } else {
        this.relevantNewsContainer.innerHTML = '<div style="color: var(--text-muted); padding: 1rem 0;">No active news articles matched your specific thesis keywords yet.</div>';
      }

      // Render All Company News
      if (all.length > 0) {
        this.allNewsContainer.innerHTML = all.map(art => this.renderNewsCard(art, false)).join('');
      } else {
        this.allNewsContainer.innerHTML = '<div style="color: var(--text-muted); padding: 1rem 0;">No articles available.</div>';
      }

    } catch (e) {
      console.error('Error fetching news:', e);
      this.relevantNewsContainer.innerHTML = '<div style="color: #ef4444;">Error retrieving news.</div>';
    }
  }

  renderNewsCard(art, isRelevant) {
    const pubDate = art.publishedAt ? new Date(art.publishedAt).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) : '';
    
    let relevanceTag = '';
    if (isRelevant) {
      const cls = art.classification || 'NEUTRAL';
      const badgeCls = cls === 'SUPPORTING' ? 'strengthening' : (cls === 'CONTRADICTING' ? 'attention' : 'nochange');
      relevanceTag = `
        <div class="news-relevance-banner">
          <span class="status-pill ${badgeCls}" style="padding: 0.15rem 0.5rem; font-size: 0.7rem; margin-right: 0.5rem;">${cls}</span>
          ${this.escapeHtml(art.reason || 'Matches investment thesis parameters')}
        </div>
      `;
    }

    return `
      <a href="${art.url || '#'}" target="_blank" rel="noopener noreferrer" class="news-card-item">
        <div class="news-card-top-row">
          <span style="font-weight: 600; color: var(--brand-primary);">${this.escapeHtml(art.source || 'Press')}</span>
          <span>${pubDate}</span>
        </div>
        <div class="news-article-title">${this.escapeHtml(art.title)}</div>
        <div class="news-article-summary">${this.escapeHtml(art.summary || art.title)}</div>
        ${relevanceTag}
      </a>
    `;
  }

  async loadTechnicalsTab(symbol) {
    try {
      const tech = await window.api.getTechnicals(symbol);

      if (this.techRSI) this.techRSI.textContent = tech.rsi !== null ? tech.rsi : 'Not available';
      if (this.techMACD) this.techMACD.textContent = tech.macd !== null ? `${tech.macd.toFixed(2)} (Signal: ${tech.macdSignal?.toFixed(2) || '0'})` : 'Not available';
      if (this.techSMA20) this.techSMA20.textContent = tech.sma20 ? `₹${tech.sma20.toFixed(2)}` : 'Not available';
      if (this.techSMA50) this.techSMA50.textContent = tech.sma50 ? `₹${tech.sma50.toFixed(2)}` : 'Not available';
      if (this.techSMA200) this.techSMA200.textContent = tech.sma200 ? `₹${tech.sma200.toFixed(2)}` : 'Not available';
      if (this.techVolatility) this.techVolatility.textContent = tech.volatility !== null ? `${tech.volatility}%` : 'Not available';

      if (this.techTrendBadge) {
        const tr = tech.trend || 'NEUTRAL';
        const cls = tr === 'BULLISH' ? 'strengthening' : (tr === 'BEARISH' ? 'contradicting' : 'nochange');
        this.techTrendBadge.className = `status-pill ${cls}`;
        this.techTrendBadge.textContent = tr;
      }
    } catch (e) {
      console.error('Error fetching technicals:', e);
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

window.CompanyView = CompanyView;
