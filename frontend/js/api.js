/**
 * Smart Watchlist — API Client
 */

const API_BASE = '/api';

class ApiClient {
  constructor() {
    this.token = localStorage.getItem('sw_token') || '';
  }

  setToken(token) {
    this.token = token;
    if (token) {
      localStorage.setItem('sw_token', token);
    } else {
      localStorage.removeItem('sw_token');
    }
  }

  async request(endpoint, options = {}) {
    const headers = {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const config = {
      ...options,
      headers
    };

    try {
      const res = await fetch(`${API_BASE}${endpoint}`, config);
      if (!res.ok) {
        let errMsg = `HTTP Error ${res.status}`;
        try {
          const errData = await res.json();
          if (errData && errData.detail) {
            errMsg = errData.detail;
          }
        } catch (_) {}
        throw new Error(errMsg);
      }
      return await res.json();
    } catch (err) {
      console.error(`API Error on ${endpoint}:`, err);
      throw err;
    }
  }

  // Health
  getHealth() {
    return this.request('/health');
  }

  // Watchlist Summary (Landing Page)
  getWatchlistSummary() {
    return this.request('/watchlist/summary');
  }

  runAllEvaluations() {
    return this.request('/evaluations/run', { method: 'POST' });
  }

  // Watchlists
  getWatchlists() {
    return this.request('/watchlists');
  }

  getWatchlist(id) {
    return this.request(`/watchlists/${id}`);
  }

  createWatchlist(name) {
    return this.request('/watchlists', {
      method: 'POST',
      body: JSON.stringify({ name })
    });
  }

  addStockToWatchlist(watchlistId, data) {
    return this.request(`/watchlists/${watchlistId}/items`, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  deleteStockFromWatchlist(watchlistId, symbol) {
    return this.request(`/watchlists/${watchlistId}/items/${encodeURIComponent(symbol)}`, {
      method: 'DELETE'
    });
  }

  // Stocks & Market Data
  searchStocks(query) {
    return this.request(`/stocks/search?q=${encodeURIComponent(query)}`);
  }

  getQuote(symbol) {
    return this.request(`/stocks/${encodeURIComponent(symbol)}`);
  }

  getHistory(symbol, range = '1M') {
    return this.request(`/stocks/${encodeURIComponent(symbol)}/history?range=${encodeURIComponent(range)}`);
  }

  getFundamentals(symbol) {
    return this.request(`/stocks/${encodeURIComponent(symbol)}/fundamentals`);
  }

  getTechnicals(symbol) {
    return this.request(`/stocks/${encodeURIComponent(symbol)}/technicals`);
  }

  getStockNews(symbol) {
    return this.request(`/stocks/${encodeURIComponent(symbol)}/news`);
  }

  // Thesis Intelligence
  getThesis(symbol) {
    return this.request(`/thesis/${encodeURIComponent(symbol)}`);
  }

  updateThesis(symbol, text, category) {
    return this.request(`/thesis/${encodeURIComponent(symbol)}`, {
      method: 'PUT',
      body: JSON.stringify({ text, category })
    });
  }

  getThesisSignals(symbol) {
    return this.request(`/thesis/${encodeURIComponent(symbol)}/signals`);
  }

  getWhatChanged(symbol) {
    return this.request(`/thesis/${encodeURIComponent(symbol)}/changes`);
  }

  evaluateThesis(symbol) {
    return this.request(`/thesis/${encodeURIComponent(symbol)}/evaluate`, {
      method: 'POST'
    });
  }
}

window.api = new ApiClient();
