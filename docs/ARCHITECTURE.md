# Architecture Documentation — Thesis Watchlist

## System Overview

Thesis Watchlist is a thesis-first stock intelligence platform built to answer the fundamental question:
**"Why am I watching this stock, what has changed since I last checked, and does that change support or contradict the reason I was watching it?"**

Unlike conventional watchlists that simply display ticker symbols and fluctuating price points, Thesis Watchlist models an investor's rationale and converts it into structured signal profiles. Real-world market feeds, quarterly SEC/MCA regulatory filings, news publications, and management commentaries are continuously ingested, passed through a significance filter, evaluated against user-defined signal directions, and aggregated into a diagnostic health status.

---

## Architectural Diagram

```
+--------------------------------------------------------------------------------+
|                             Frontend (Vanilla JS SPA)                          |
|  [Landing View (Summary)] -> [My Watchlist] -> [Company Hub] -> [What Changed] |
|              ^                                          ^                      |
|              | HTTP REST                                | WebSockets           |
+--------------v------------------------------------------v----------------------+
                                     |
+------------------------------------v-------------------------------------------+
|                          FastAPI Backend Application                           |
|                                                                                |
|  +---------------------+  +---------------------+  +------------------------+  |
|  |   API Layer (REST)  |  |  WebSocket Manager  |  |  Security & Auth (JWT) |  |
|  | /stocks, /thesis... |  |  Live Quote Stream  |  |  Multi-User DB Scoped  |  |
|  +----------+----------+  +----------+----------+  +-----------+------------+  |
|             |                        |                         |               |
|  +----------v------------------------v-------------------------v------------+  |
|  |                       Thesis Intelligence Engine                         |  |
|  |                                                                          |  |
|  |  [Thesis Text] -> [Thesis Interpreter] -> [Structured Signals Profile]   |  |
|  |                                                       |                  |  |
|  |  [Historical Snapshots] vs [Live Feeds]               |                  |  |
|  |                                   |                   v                  |  |
|  |               [Change Detection Engine (Significance Filter)]            |  |
|  |                                   |                                      |  |
|  |               [Evidence Classifier (Supporting / Contradicting)]         |  |
|  |                                   |                                      |  |
|  |               [Status Synthesis & Explainability Formatter]              |  |
|  +-----------------------------------+--------------------------------------+  |
|                                      |                                         |
|  +-----------------------------------v--------------------------------------+  |
|  |                     Provider Abstraction Layer                           |  |
|  |                                                                          |  |
|  |     MarketDataProvider (Base)       NewsProvider (Base)                  |  |
|  |     +-- YahooMarketDataProvider     +-- YahooAndRssNewsProvider          |  |
|  |     +-- Upstox/Zerodha (Extensible) +-- Finnhub/NewsAPI (Extensible)     |  |
|  |                                                                          |  |
|  |  Features: In-memory TTL Caching, Rate-limit backoff, Freshness tracking |  |
|  +-----------------------------------+--------------------------------------+  |
|                                      |                                         |
|  +-----------------------------------v--------------------------------------+  |
|  |                     Database & Persistence (SQLAlchemy)                  |  |
|  |  PostgreSQL / SQLite fallback (12 Normalized Models, Alembic Migrations) |  |
|  +--------------------------------------------------------------------------+  |
+--------------------------------------------------------------------------------+
```

---

## Component Architecture

### 1. Presentation Layer (Frontend)
- **Technology**: Vanilla HTML5, CSS3, ES6+ Modular JavaScript.
- **Styling Architecture**: Tailored design system (`main.css`, `components.css`, `pages.css`) utilizing dark mode tokens, high-contrast typography (`Plus Jakarta Sans`, `JetBrains Mono`), glassmorphic panels, and state-driven color badges.
- **SPA Routing**: Event-based client router responding to hash navigation (`#/home`, `#/watchlist`, `#/company/:symbol`, `#/changes/:symbol`) and browser history manipulation without full-page reloads.
- **Real-Time Layer**: WebSocket client receiving asynchronous quote updates and updating DOM nodes dynamically.
- **Charts Engine**: Native Canvas financial chart with Retina high-DPI scaling, area fill gradients, crosshair tracking, and responsive tooltips.

### 2. Application Layer (FastAPI Backend)
- **Modular Routers**:
  - `auth.py`: Multi-user registration, bcrypt password hashing, JWT bearer issuance, profile resolution.
  - `stocks.py`: Autocomplete company search, real-time quotes, historical OHLCV data, fundamental ratios, technical indicator analysis, company news feeds.
  - `watchlists.py`: Watchlist lifecycle management, item addition with integrated thesis derivation, live quote aggregation.
  - `theses.py`: Retrieval, manual updates, signal listings, and on-demand "What Changed" evaluation execution.
  - `summary.py`: High-level landing page metrics aggregation (`thesisChangedCount`, `needsAttentionCount`, `noChangeCount`).
  - `ws.py`: WebSocket connection management and symbol subscription broadcasting.

### 3. Thesis Intelligence & Decision Engine
- **Interpreter (`services/thesis/interpreter.py`)**: Converts unstructured investor thesis text into structured attributes:
  - Business entities (e.g. Jio, EV, Cloud, Semiconductor, Retail).
  - Investment themes (Growth, Valuation, Demand Recovery, Margin Expansion, Deleveraging).
  - Quantitative and qualitative signals with directional preferences (`POSITIVE` / `NEGATIVE` / `NEUTRAL`).
- **Snapshot Service (`services/snapshot/snapshot_service.py`)**: Persists `MarketSnapshot` and `FundamentalSnapshot` instances at every evaluation cycle to enable longitudinal baseline comparisons (`Today` vs `Last Check` vs `Previous Filing`).
- **Change Detection Engine (`services/change_detection/detector.py`)**: Implements significance heuristics across market price swings, valuation multiple variances, margin shifts, quarterly revenue variance, and high-impact press releases.
- **Evidence Classifier (`services/intelligence/evidence_classifier.py`)**: Evaluates detected changes against expected signal trajectories to assign classifications: `SUPPORTING`, `CONTRADICTING`, `NEUTRAL`, `UNCERTAIN`.
- **Status Synthesizer (`services/evaluation/evaluator.py`)**: Aggregates classified evidence to assign the high-level user status:
  - 🟢 `THESIS STRENGTHENING`
  - 🟠 `NEEDS ATTENTION`
  - ⚪ `NO MEANINGFUL CHANGE`
  Produces explainability narratives (e.g. *"Your thesis needs attention because 2 relevant signals strengthened while 2 relevant signals weakened"*).

### 4. Market & News Provider Abstraction
- Abstract base interfaces (`MarketDataProvider`, `NewsProvider`) decouple external vendor APIs from business logic.
- Production implementations (`YahooMarketDataProvider`, `YahooAndRssNewsProvider`) support Indian equities (`.NS`, `.BO`) as well as global tickers.
- Multi-tier TTL cache prevents rate-limiting and optimizes response latency.
- Strict data provenance: Every market payload flags freshness (`LIVE`, `DELAYED (15 min)`, `AS OF [timestamp]`). Missing values are rendered as "Not available" rather than simulated defaults.
