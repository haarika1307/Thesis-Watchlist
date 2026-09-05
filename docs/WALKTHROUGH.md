# System Walkthrough & Operational Guide — Smart Watchlist

## 1. What Was Built

Smart Watchlist is a full-stack, thesis-first financial intelligence platform. It replaces the passive, ticker-and-price paradigm of standard stock watchlists with an active rationale-tracking engine.

The platform continuously answers three core questions:
1. **Why am I watching this stock?**
2. **What has changed in the real world since I last checked?**
3. **Does that change support or contradict the reason I was watching it?**

The application enforces a strict UX hierarchy:
- **Landing Screen**: Displays a high-level summary of the watchlist state (Last Checked, Thesis Changed, Needs Attention, No Change) and a `GO GROW →` button. Individual stocks are **never** displayed on this first screen.
- **My Watchlist**: Shows the user's real stocks with live prices, percentage change, and status indicators (🟢 Thesis strengthening, 🟠 Thesis needs attention, ⚪ No meaningful change).
- **Add Stock Experience**: Allows searching real companies, selecting a category, and writing an investment thesis in natural language.
- **Company Detail Hub**: Tabbed interface featuring Thesis (default), Overview, Fundamentals, News, and Technicals.
- **What Changed?**: The core differentiator page that breaks down real-world evidence into Supporting vs Working Against categories, accompanied by a diagnostic explanation.

---

## 2. Why It Was Built

Traditional stock market tools suffer from severe cognitive fragmentation:
- Investors record ticker symbols into watchlists but forget their original thesis weeks later.
- Reviewing positions requires manually combing through news feeds, quarterly corporate filings, balance sheets, and charts to discern if something meaningful occurred.
- Users struggle to weigh positive top-line growth against compressing operating margins or rising debt.

Smart Watchlist resolves this by establishing a clear causal chain:
$$\text{User Thesis} \longrightarrow \text{Structured Signals} \longrightarrow \text{Real Data Feeds} \longrightarrow \text{Change Detection} \longrightarrow \text{Evidence Classification} \longrightarrow \text{Diagnostic Status}$$

---

## 3. Architecture & Interaction

```
[User Browser]
       |
       |  HTTP & WebSockets
       v
[FastAPI Application Server]
  |-- API Routers (/stocks, /watchlists, /thesis, /summary, /auth)
  |-- WebSocket Stream Manager (/ws/market)
  |-- Thesis Intelligence Subsystem:
  |     |-- Thesis Interpreter (NLP/Regex Entity & Theme Parser)
  |     |-- Change Detection Engine (Significance & Baseline Filters)
  |     |-- Evidence Classifier (Directional Logic)
  |     \-- Evaluator & Explainability Generator
  |-- Provider Abstraction Layer:
  |     |-- MarketDataProvider (Yahoo Finance / yfinance + Cache)
  |     \-- NewsProvider (Yahoo Finance + Google News RSS)
  \-- Persistence Layer:
        \-- SQLAlchemy ORM -> PostgreSQL / SQLite
```

### Component Interaction Flow:
1. **Stock Ingestion**: When the user adds a stock (e.g. `RELIANCE.NS`), `ThesisInterpreter` extracts themes (Growth, Valuation, Margin, etc.), isolates business units (e.g. `Jio`), and generates directional signal definitions.
2. **Data Collection**: `MarketDataProvider` and `NewsProvider` query real financial APIs to retrieve quotes, historical candles, balance sheet ratios, and news.
3. **Snapshot Capture**: `SnapshotService` records initial `MarketSnapshot` and `FundamentalSnapshot` rows to provide an immutable baseline for future comparisons.
4. **Change Detection**: `ChangeDetectionEngine` compares current values against baseline values and applies significance thresholds (e.g., price swings > 2.5%, margin shifts > 50 bps, high-impact deal announcements).
5. **Evidence Classification**: `EvidenceClassifier` maps each significant change against the thesis signal's desired direction (`POSITIVE` or `NEGATIVE`) to classify it as `SUPPORTING` or `CONTRADICTING`.
6. **Diagnostic Synthesis**: `ThesisEvaluator` computes the aggregate thesis status (🟢 `STRENGTHENING`, 🟠 `NEEDS_ATTENTION`, ⚪ `NO_CHANGE`) and crafts an explainable diagnosis.

---

## 4. Database Models

The schema contains 12 normalized SQLAlchemy models:
1. **`User`**: Account identity with bcrypt hashing and JWT bearer authentication.
2. **`Watchlist`**: User-scoped portfolio container.
3. **`WatchlistItem`**: Unique ticker symbol mapping to a watchlist.
4. **`Thesis`**: Core rationale, category, health status, and evaluation timestamp.
5. **`ThesisSignal`**: Granular quantitative/qualitative metrics monitored for each thesis.
6. **`MarketSnapshot`**: Time-series historical record of price, change, volume, volatility, and market cap.
7. **`FundamentalSnapshot`**: Time-series record of P/E, P/B, EPS, ROE, ROCE, revenue, margins, EBITDA, debt, and cash flows.
8. **`NewsArticle`**: Ingested financial news articles with URL, source, publication date, and summary.
9. **`NewsRelevance`**: Many-to-many relationship scoring and classifying news articles against specific theses.
10. **`Evidence`**: Verified changes with previous vs current values, delta percentage, classification (`SUPPORTING` / `CONTRADICTING`), confidence, and explanation.
11. **`Evaluation`**: Historical record of thesis evaluation runs with supporting/contradicting counts and narrative summaries.
12. **`WatchlistEvaluation`**: Portfolio-level snapshot recording `thesisChangedCount`, `needsAttentionCount`, and `noChangeCount`.

---

## 5. Frontend Design & Technology

- **Pure Vanilla Stack**: Built using standard HTML5, CSS3, and modern modular JavaScript (ES6+). Zero reliance on React, TypeScript, or Tailwind.
- **Visual Design**: Dark-mode palette (`#080b11`, `#0f1422`, `#151b2d`) with subtle border highlights, glowing emerald and amber status pills, and high-contrast typography (`Plus Jakarta Sans` for interface, `JetBrains Mono` for financial metrics).
- **Responsive Financial Chart**: Custom HTML5 Canvas charting engine with Retina display support, price gridlines, area gradient fills, and interactive crosshair hover inspection.
- **Single Page Application (SPA)**: Custom hash router (`#/home`, `#/watchlist`, `#/company/:symbol`, `#/changes/:symbol`) providing instant view transitions without page refreshes.
- **Real-Time Data**: WebSocket streaming manager that automatically pushes live price and volume updates to active DOM cards.

---

## 6. Real Market & News Integration

- **No Mock or Fake Data**: Quotes, candle history, balance sheet ratios, and news articles are sourced directly from live financial data feeds (Yahoo Finance API & Google News RSS).
- **Symbol Normalization**: Automatically handles Indian equities (NSE `.NS`, BSE `.BO`) as well as US/Global tickers (e.g. `AAPL`, `MSFT`).
- **Data Provenance**: All market responses include a freshness badge (`LIVE`, `DELAYED (15 min)`, `AS OF [timestamp]`). If a provider does not supply a metric, the UI renders **"Not available"** rather than inventing a number.
- **Intelligent Caching**: In-memory multi-tier TTL cache (60s for quotes, 5m for charts, 1hr for fundamentals, 15m for news) prevents upstream rate-limiting while maintaining freshness.

---

## 7. How to Run the Project

### Option A: Local Run (Direct Python)

1. **Activate Virtual Environment & Install Dependencies**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Environment Variables**:
   Copy `.env.example` to `.env` (the defaults work immediately with SQLite):
   ```bash
   cp .env.example .env
   ```

3. **Start the Application Server**:
   ```bash
   ./venv/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
   ```

4. **Access the Application**:
   Open [http://localhost:8000](http://localhost:8000) in your web browser.

---

### Option B: Docker Compose (Production PostgreSQL)

1. **Run with Docker Compose**:
   ```bash
   docker-compose up --build -d
   ```

2. **Access**:
   Navigate to [http://localhost:8000](http://localhost:8000). The database runs in PostgreSQL 16 on port 5432.

---

## 8. Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./smart_watchlist.db` | Database connection URI (PostgreSQL or SQLite) |
| `JWT_SECRET` | *Secure random string* | Secret key for signing JWT tokens |
| `ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `10080` (7 days) | Token expiration duration |
| `MARKET_DATA_PROVIDER` | `yahoo` | Active market data provider (`yahoo`, `upstox`, `zerodha`) |
| `MARKET_DATA_API_KEY` | *(empty)* | Optional API key for market provider |
| `NEWS_PROVIDER` | `yahoo` | Active news provider (`yahoo`, `newsapi`, `finnhub`) |
| `NEWS_API_KEY` | *(empty)* | Optional API key for news provider |
| `LLM_PROVIDER` | `builtin` | Intelligence parser mode (`builtin`, `openai`, `gemini`) |
| `LLM_API_KEY` | *(empty)* | Optional LLM API key |
| `FRONTEND_ORIGIN` | `*` | Allowed CORS origins |
| `PORT` | `8000` | Application HTTP port |

---

## 9. Known Limitations & Future Improvements

### Known Limitations:
1. **Free Market Provider Delays**: Yahoo Finance market data for Indian equities (NSE/BSE) is typically delayed by 15 minutes during trading hours. This is accurately reflected via the `DELAYED (15 min)` freshness tag.
2. **Direct Upstox/Zerodha Authorization**: Connecting to broker APIs like Upstox or Zerodha Kite requires user-specific daily TOTP / OAuth login sessions. The provider abstraction layer is prepared for these connectors.

### Future Roadmap:
1. **Broker Integration**: Native OAuth connection for Zerodha Kite Connect, Upstox, and Angel One for zero-latency live tick streaming.
2. **Audio Earnings Call Ingestion**: Speech-to-text pipeline that transcribes quarterly investor conference calls and extracts management tone directly into thesis signals.
3. **Multi-Portfolio Partitioning**: Organizing separate watchlists for Long-Term Compounders, Deep Value Turnarounds, and Special Situations.
