/**
 * Thesis Watchlist — Landing Page Component (Home View)
 *
 * STRICT RULE: This first screen is a summary of the state of the watchlist.
 * Individual stocks MUST NOT be displayed here.
 * Stocks appear ONLY after clicking 'GO GROW'.
 */

class HomeView {
  constructor() {
    this.container = document.getElementById('home-view');
    this.lastCheckedEl = document.getElementById('home-last-checked');
    this.changedCountEl = document.getElementById('count-thesis-changed');
    this.attentionCountEl = document.getElementById('count-needs-attention');
    this.noChangeCountEl = document.getElementById('count-no-change');
    this.btnGoGrow = document.getElementById('btn-go-grow');

    this.initEvents();
  }

  initEvents() {
    if (this.btnGoGrow) {
      this.btnGoGrow.addEventListener('click', () => {
        window.appState.setView('watchlist');
      });
    }
  }

  async loadSummary() {
    try {
      const summary = await window.api.getWatchlistSummary();
      window.appState.summaryData = summary;
      this.render(summary);
    } catch (err) {
      console.error('Failed to load watchlist summary:', err);
      this.render({
        lastCheckedAt: new Date().toISOString(),
        thesisChangedCount: 0,
        needsAttentionCount: 0,
        noChangeCount: 0
      });
    }
  }

  render(summary) {
    if (this.lastCheckedEl) {
      let formattedDate = 'JUST NOW';
      if (summary.lastCheckedAt) {
        try {
          const d = new Date(summary.lastCheckedAt);
          formattedDate = d.toLocaleDateString('en-GB', {
            day: 'numeric',
            month: 'short',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
          });
        } catch (_) {}
      }
      this.lastCheckedEl.textContent = `LAST CHECKED: ${formattedDate}`;
    }

    if (this.changedCountEl) {
      this.changedCountEl.textContent = summary.thesisChangedCount ?? 0;
    }
    if (this.attentionCountEl) {
      this.attentionCountEl.textContent = summary.needsAttentionCount ?? 0;
    }
    if (this.noChangeCountEl) {
      this.noChangeCountEl.textContent = summary.noChangeCount ?? 0;
    }
  }
}

window.HomeView = HomeView;
