/**
 * Smart Watchlist — What Changed Page Component (Core Product Feature)
 */

class ChangesView {
  constructor() {
    this.container = document.getElementById('changes-view');
    this.thesisTextEl = document.getElementById('changes-thesis-text');
    this.backToCompanyBtn = document.getElementById('btn-changes-back');
    this.btnRunReevaluation = document.getElementById('btn-re-evaluate');

    this.supportingContainer = document.getElementById('evidence-supporting-list');
    this.contradictingContainer = document.getElementById('evidence-contradicting-list');
    this.neutralContainer = document.getElementById('evidence-neutral-list');

    this.statusBadgeEl = document.getElementById('synthesis-status-badge');
    this.countsLineEl = document.getElementById('synthesis-counts-line');
    this.explanationEl = document.getElementById('synthesis-explanation-text');

    this.activeSymbol = null;

    this.initEvents();
  }

  initEvents() {
    if (this.backToCompanyBtn) {
      this.backToCompanyBtn.addEventListener('click', (e) => {
        e.preventDefault();
        if (this.activeSymbol) {
          window.appState.setView('company', { symbol: this.activeSymbol });
        } else {
          window.appState.setView('watchlist');
        }
      });
    }

    if (this.btnRunReevaluation) {
      this.btnRunReevaluation.addEventListener('click', async () => {
        if (!this.activeSymbol) return;
        this.btnRunReevaluation.textContent = 'Evaluating Live Data...';
        this.btnRunReevaluation.disabled = true;
        try {
          await window.api.evaluateThesis(this.activeSymbol);
          await this.loadWhatChanged(this.activeSymbol);
        } catch (e) {
          console.error('Error re-evaluating thesis:', e);
        } finally {
          this.btnRunReevaluation.textContent = '🔄 Re-evaluate Live Signals';
          this.btnRunReevaluation.disabled = false;
        }
      });
    }
  }

  async loadWhatChanged(symbol) {
    this.activeSymbol = symbol;

    if (this.supportingContainer) this.supportingContainer.innerHTML = '<div class="spinner"></div>';
    if (this.contradictingContainer) this.contradictingContainer.innerHTML = '<div class="spinner"></div>';
    if (this.neutralContainer) this.neutralContainer.innerHTML = '<div class="spinner"></div>';

    try {
      const data = await window.api.getWhatChanged(symbol);
      this.render(data);
    } catch (err) {
      console.error('Failed to load What Changed analysis:', err);
      if (this.supportingContainer) this.supportingContainer.innerHTML = `<div style="color: #ef4444;">${err.message || 'Error running evaluation.'}</div>`;
    }
  }

  render(data) {
    // 1. User Thesis Text
    if (this.thesisTextEl) {
      this.thesisTextEl.textContent = `"${data.thesisText}"`;
    }

    // 2. Supporting Evidence
    const sup = data.supportingEvidence || [];
    if (this.supportingContainer) {
      if (sup.length > 0) {
        this.supportingContainer.innerHTML = sup.map(ev => this.renderEvidenceCard(ev, 'supporting')).join('');
      } else {
        this.supportingContainer.innerHTML = `
          <div style="background: var(--bg-card); border: 1px dashed var(--border-subtle); border-radius: var(--radius-md); padding: 1.5rem; text-align: center; color: var(--text-muted);">
            No currently observed signals satisfy positive validation thresholds for this thesis.
          </div>
        `;
      }
    }

    // 3. Working Against / Contradicting Evidence
    const con = data.contradictingEvidence || [];
    if (this.contradictingContainer) {
      if (con.length > 0) {
        this.contradictingContainer.innerHTML = con.map(ev => this.renderEvidenceCard(ev, 'contradicting')).join('');
      } else {
        this.contradictingContainer.innerHTML = `
          <div style="background: var(--bg-card); border: 1px dashed var(--border-subtle); border-radius: var(--radius-md); padding: 1.5rem; text-align: center; color: var(--text-muted);">
            No contradictory signals or negative variances detected.
          </div>
        `;
      }
    }

    // 4. Neutral / Other Relevant
    const neu = data.neutralEvidence || [];
    if (this.neutralContainer) {
      if (neu.length > 0) {
        this.neutralContainer.innerHTML = neu.map(ev => this.renderEvidenceCard(ev, 'neutral')).join('');
      } else {
        this.neutralContainer.innerHTML = `
          <div style="background: var(--bg-card); border: 1px dashed var(--border-subtle); border-radius: var(--radius-md); padding: 1rem; text-align: center; color: var(--text-muted);">
            No secondary signals in neutral state.
          </div>
        `;
      }
    }

    // 5. Overall Synthesis & Explainability
    const st = data.status || 'NO_CHANGE';
    let statusClass = 'nochange';
    let statusTitle = '⚪ NO MEANINGFUL CHANGE';

    if (st === 'STRENGTHENING') {
      statusClass = 'strengthening';
      statusTitle = '🟢 THESIS STRENGTHENING';
    } else if (st === 'NEEDS_ATTENTION') {
      statusClass = 'attention';
      statusTitle = '🟠 NEEDS ATTENTION';
    }

    if (this.statusBadgeEl) {
      this.statusBadgeEl.className = `status-pill ${statusClass}`;
      this.statusBadgeEl.textContent = statusTitle;
    }

    if (this.countsLineEl) {
      this.countsLineEl.textContent = `${data.supportingCount} signal${data.supportingCount !== 1 ? 's' : ''} support your thesis • ${data.contradictingCount} signal${data.contradictingCount !== 1 ? 's' : ''} work against it`;
    }

    if (this.explanationEl) {
      this.explanationEl.textContent = data.summary;
    }
  }

  renderEvidenceCard(ev, type) {
    const isSup = type === 'supporting';
    const isCon = type === 'contradicting';

    const verdictBadge = isSup
      ? '<span class="evidence-verdict-badge supporting">✓ Supports your thesis</span>'
      : (isCon ? '<span class="evidence-verdict-badge contradicting">⚠ Works against your thesis</span>' : '<span class="evidence-verdict-badge" style="color: var(--text-muted);">ℹ Contextual / Neutral</span>');

    const prevDisplay = ev.previousValue ? `<span class="evidence-val-prev">${this.escapeHtml(ev.previousValue)}</span>` : '';
    const arrow = isSup ? '↑' : (isCon ? '↓' : '→');

    const formattedTime = ev.timestamp ? new Date(ev.timestamp).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) : 'Recent observation';

    return `
      <div class="evidence-card ${type}">
        <div class="evidence-card-top">
          <span class="evidence-signal-name">${this.escapeHtml(ev.signalName)}</span>
          <span class="badge-freshness">${this.escapeHtml(ev.sourceType)}</span>
        </div>

        <div class="evidence-values-comparison">
          ${prevDisplay}
          <span style="font-weight: 700; color: ${isSup ? 'var(--color-strengthening)' : (isCon ? 'var(--color-attention)' : 'var(--text-muted)')}; font-size: 1.1rem;">${arrow}</span>
          <span class="evidence-val-curr">${this.escapeHtml(ev.currentValue || '')}</span>
          ${ev.changeValue ? `<span style="font-size: 0.85rem; color: var(--text-secondary);">(${this.escapeHtml(ev.changeValue)})</span>` : ''}
        </div>

        <div>
          ${verdictBadge}
        </div>

        <div class="evidence-explanation">
          ${this.escapeHtml(ev.explanation)}
        </div>

        <div class="evidence-footer">
          <span>Source: ${this.escapeHtml(ev.sourceId || ev.sourceType)}</span>
          <span>${formattedTime}</span>
        </div>
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

window.ChangesView = ChangesView;
