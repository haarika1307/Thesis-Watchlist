/**
 * Smart Watchlist — Central Application State
 */

class AppState {
  constructor() {
    this.currentView = 'home'; // 'home', 'watchlist', 'company', 'changes'
    this.selectedSymbol = null;
    this.currentWatchlist = null;
    this.watchlists = [];
    this.summaryData = null;
    this.listeners = {};
    this.ws = null;
    this.subscribedSymbols = new Set();
  }

  on(event, callback) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(callback);
  }

  emit(event, data) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(cb => {
        try {
          cb(data);
        } catch (e) {
          console.error(`Error in listener for ${event}:`, e);
        }
      });
    }
  }

  setView(viewName, params = {}) {
    this.currentView = viewName;
    if (params.symbol) {
      this.selectedSymbol = params.symbol;
    }
    this.emit('viewChange', { view: viewName, params });
  }

  updateStockQuote(symbol, quoteData) {
    // Update active watchlist item if matches
    if (this.currentWatchlist && this.currentWatchlist.items) {
      const item = this.currentWatchlist.items.find(i => i.symbol.toUpperCase() === symbol.toUpperCase());
      if (item) {
        item.price = quoteData.price;
        item.change = quoteData.change;
        item.percentageChange = quoteData.percentageChange;
        item.volume = quoteData.volume;
        this.emit('stockQuoteUpdated', { symbol, quoteData });
      }
    }
    // Also emit symbol update for company page
    if (this.selectedSymbol && this.selectedSymbol.toUpperCase() === symbol.toUpperCase()) {
      this.emit('activeStockQuoteUpdated', quoteData);
    }
  }

  initWebSocket() {
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      const wsUrl = `${protocol}//${host}/api/ws/market`;

      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('Market WebSocket connection established.');
        if (this.subscribedSymbols.size > 0) {
          this.subscribeSymbols(Array.from(this.subscribedSymbols));
        }
      };

      this.ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'QUOTE_UPDATE') {
            this.updateStockQuote(msg.symbol, msg.data);
          }
        } catch (e) {
          console.error('Error handling WS message:', e);
        }
      };

      this.ws.onclose = () => {
        console.log('Market WebSocket disconnected. Reconnecting in 5s...');
        setTimeout(() => this.initWebSocket(), 5000);
      };

      this.ws.onerror = (err) => {
        console.warn('Market WebSocket warning:', err);
      };
    } catch (e) {
      console.warn('Could not initialize WebSocket:', e);
    }
  }

  subscribeSymbols(symbols) {
    symbols.forEach(s => this.subscribedSymbols.add(s));
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        action: 'subscribe',
        symbols: Array.from(this.subscribedSymbols)
      }));
    }
  }
}

window.appState = new AppState();
