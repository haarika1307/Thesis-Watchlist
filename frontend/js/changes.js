/**
 * Thesis Watchlist — What Changed Page Component (Core Product Feature)
 */

class ChangesView {
  constructor() {
    this.container = document.getElementById('changes-view');
    this.thesisTextEl = document.getElementById('changes-thesis-text');
    this.backToCompanyBtn = document.getElementById('btn-changes-back');
    this.btnRunReevaluation = document.getElementById('btn-re-evaluate');
    this.lastCheckedNoteEl = document.getElementById('changes-view-last-checked-note');
    this.objectiveCategoriesContainer = document.getElementById('objective-changes-categories-container');

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

    if (this.objectiveCategoriesContainer) this.objectiveCategoriesContainer.innerHTML = '<div class="spinner"></div>';
    if (this.supportingContainer) this.supportingContainer.innerHTML = '<div class="spinner"></div>';
    if (this.contradictingContainer) this.contradictingContainer.innerHTML = '<div class="spinner"></div>';
    if (this.neutralContainer) this.neutralContainer.innerHTML = '<div class="spinner"></div>';

    try {
      const data = await window.api.getWhatChanged(symbol);
      this.render(data);
    } catch (err) {
      console.error('Failed to load What Changed analysis:', err);
      if (this.objectiveCategoriesContainer) this.objectiveCategoriesContainer.innerHTML = `<div style="color: #ef4444;">${err.message || 'Error running evaluation.'}</div>`;
    }
  }

  render(data) {
    // 0. Last Checked Timestamp note
    if (this.lastCheckedNoteEl && data.lastCheckedAt) {
      const dt = new Date(data.lastCheckedAt);
      this.lastCheckedNoteEl.textContent = `Comparing current state against your last check on ${dt.toLocaleDateString()} at ${dt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}.`;
    }

    // 1. PART 1: OBJECTIVE MEANINGFUL CHANGES BY CATEGORY (MARKET, FUNDAMENTALS, COMPANY, NEWS)
    const objChanges = data.objectiveChanges || [];
    if (this.objectiveCategoriesContainer) {
      if (objChanges.length === 0) {
        this.objectiveCategoriesContainer.innerHTML = `
          <div style="background: var(--bg-card); border: 1px dashed var(--border-subtle); border-radius: var(--radius-md); padding: 2rem; text-align: center; color: var(--text-muted);">
            ⚪ No objectively meaningful changes detected across Market, Fundamentals, Company events, or News since your last check.
          </div>
        `;
      } else {
        const categories = ['MARKET', 'FUNDAMENTALS', 'COMPANY', 'NEWS'];
        const grouped = {};
        categories.forEach(c => grouped[c] = []);

        objChanges.forEach(ch => {
          const cat = (ch.category || 'MARKET').toUpperCase();
          if (!grouped[cat]) grouped[cat] = [];
          grouped[cat].push(ch);
        });

        let catHtml = '';
        categories.forEach(cat => {
          const items = grouped[cat];
          if (items.length === 0) return;

          catHtml += `
            <div class="objective-category-box">
              <div class="objective-category-title-bar">
                <span class="objective-category-header-text">${cat}</span>
                <span class="badge-freshness">${items.length} shift${items.length !== 1 ? 's' : ''} detected</span>
              </div>
              <div class="normal-changes-grid">
                ${items.map(ch => this.renderObjectiveChangeCard(ch)).join('')}
              </div>
            </div>
          `;
        });

        this.objectiveCategoriesContainer.innerHTML = catHtml || `
          <div style="background: var(--bg-card); border: 1px dashed var(--border-subtle); border-radius: var(--radius-md); padding: 1.5rem; text-align: center; color: var(--text-muted);">
            No categorized changes found.
          </div>
        `;
      }
    }

    // 2. User Thesis Text
    if (this.thesisTextEl) {
      this.thesisTextEl.textContent = `"${data.thesisText}"`;
    }

    // 3. Supporting Evidence
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

    // 4. Working Against / Contradicting Evidence
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

    // 5. Neutral / Not Thesis-Relevant
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

    // 6. Overall Synthesis & Explainability
    const st = data.status || 'NO_MEANINGFUL_CHANGE';
    let statusClass = 'nochange';
    let statusTitle = '⚪ NO MEANINGFUL CHANGE';

    if (st === 'THESIS_STRENGTHENING' || st === 'STRENGTHENING') {
      statusClass = 'strengthening';
      statusTitle = '🟢 MEANINGFUL CHANGE / THESIS STRENGTHENING';
    } else if (st === 'THESIS_NEEDS_ATTENTION' || st === 'NEEDS_ATTENTION') {
      statusClass = 'attention';
      statusTitle = '🟠 THESIS NEEDS ATTENTION';
    } else if (st === 'MEANINGFUL_CHANGE' || data.hasMeaningfulChange) {
      statusClass = 'meaningful';
      statusTitle = '🔵 MEANINGFUL CHANGE';
    }

    if (this.statusBadgeEl) {
      this.statusBadgeEl.className = `status-pill ${statusClass}`;
      this.statusBadgeEl.textContent = statusTitle;
    }

    if (this.countsLineEl) {
      this.countsLineEl.textContent = `${data.meaningfulChangeCount || objChanges.length} meaningful changes detected • ${data.supportingCount} support thesis • ${data.contradictingCount} work against it`;
    }

    if (this.explanationEl) {
      this.explanationEl.textContent = data.summary;
    }
  }

  renderObjectiveChangeCard(ch) {
    const mag = ch.magnitude || (ch.changePercentage !== null && ch.changePercentage !== undefined ? `${ch.changePercentage > 0 ? '↑ ' : '↓ '}${Math.abs(ch.changePercentage)}%` : 'Shift detected');
    let magClass = 'neutral';
    if (mag.includes('↑') || (ch.changePercentage && ch.changePercentage > 0)) magClass = 'up';
    else if (mag.includes('↓') || (ch.changePercentage && ch.changePercentage < 0)) magClass = 'down';

    const baselineText = ch.previousValue ? `Previous: ${ch.previousValue} → Current: ${ch.currentValue}` : `Current: ${ch.currentValue}`;

    return `
      <div class="normal-change-card">
        <div class="normal-change-top">
          <span class="normal-change-name">${this.escapeHtml(ch.signalName)}</span>
          <span class="badge-freshness">${this.escapeHtml(ch.sourceType || 'METRIC')}</span>
        </div>
        <div class="normal-change-metric-row">
          <span class="normal-change-magnitude ${magClass}">${this.escapeHtml(mag)}</span>
        </div>
        <div class="normal-change-baseline">${this.escapeHtml(baselineText)}</div>
        <div class="normal-change-reason"><strong>Why meaningful:</strong> ${this.escapeHtml(ch.significanceReason || 'Material threshold exceeded since last check.')}</div>
      </div>
    `;
  }

  renderEvidenceCard(ev, type) {
    const isSup = type === 'supporting';
    const isCon = type === 'contradicting';

    const verdictBadge = isSup
      ? '<span class="evidence-verdict-badge supporting">✓ Supports your thesis</span>'
      : (isCon 
          ? '<span class="evidence-verdict-badge contradicting">⚠ Works against your thesis</span>' 
          : '<span class="evidence-verdict-badge neutral">ℹ Contextual / Neutral</span>');

    const arrow = isSup ? '↑' : (isCon ? '↓' : '→');
    const accentColor = isSup 
      ? 'var(--color-strengthening)' 
      : (isCon ? 'var(--color-attention)' : 'var(--text-muted)');

    // Format primary stat cleanly (e.g. 8%, 5.2%, 2.1%, or valuation multiple)
    let displayStat = '';
    const isHeadline = ev.sourceType === 'NEWS' || (ev.currentValue && ev.currentValue.length > 30);

    if (ev.changePercentage !== null && ev.changePercentage !== undefined && ev.changePercentage !== 0) {
      displayStat = `${Math.abs(ev.changePercentage).toFixed(1)}%`;
    } else if (ev.changeValue && (ev.changeValue.includes('%') || ev.changeValue.startsWith('+') || ev.changeValue.startsWith('-'))) {
      displayStat = ev.changeValue.replace('+', '').replace('-', '').trim();
    } else if (ev.currentValue && (ev.currentValue.includes('x') || ev.currentValue.includes('%'))) {
      displayStat = ev.currentValue;
    }

    const formattedTime = ev.timestamp 
      ? new Date(ev.timestamp).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) 
      : 'Recent observation';

    let heroHtml = '';
    if (displayStat && !isHeadline) {
      heroHtml = `
        <div class="evidence-metric-hero">
          <span class="evidence-hero-arrow" style="color: ${accentColor};">${arrow}</span>
          <span class="evidence-hero-value" style="color: ${accentColor};">${this.escapeHtml(displayStat)}</span>
          ${ev.previousValue ? `<span class="evidence-hero-baseline">from ${this.escapeHtml(ev.previousValue)}</span>` : ''}
        </div>
      `;
    } else if (isHeadline) {
      heroHtml = `
        <div class="evidence-metric-hero textual">
          <span class="evidence-hero-arrow" style="color: ${accentColor};">${arrow}</span>
          <span class="evidence-hero-textual">${this.escapeHtml(ev.currentValue)}</span>
        </div>
      `;
    } else {
      heroHtml = `
        <div class="evidence-metric-hero">
          <span class="evidence-hero-arrow" style="color: ${accentColor};">${arrow}</span>
          <span class="evidence-hero-value" style="color: ${accentColor};">${this.escapeHtml(ev.currentValue || '')}</span>
        </div>
      `;
    }

    // Source display cleanup
    let sourceLabel = ev.sourceId || ev.sourceType;
    if (sourceLabel.startsWith('http')) {
      try {
        const u = new URL(sourceLabel);
        sourceLabel = u.hostname.replace('www.', '');
      } catch (e) {
        sourceLabel = 'News Wire';
      }
    }

    return `
      <div class="evidence-card ${type}">
        <div class="evidence-card-top">
          <span class="evidence-signal-name">${this.escapeHtml(ev.signalName)}</span>
          <span class="badge-freshness">${this.escapeHtml(ev.sourceType || 'METRIC')}</span>
        </div>

        ${heroHtml}

        <div class="evidence-verdict-row">
          ${verdictBadge}
        </div>

        ${ev.explanation ? `
          <div class="evidence-explanation">
            ${this.escapeHtml(ev.explanation)}
          </div>
        ` : ''}

        <div class="evidence-footer">
          <span title="${this.escapeHtml(ev.sourceId || '')}">Source: ${this.escapeHtml(sourceLabel)}</span>
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
