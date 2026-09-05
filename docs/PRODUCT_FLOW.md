# Product Flow — Thesis Watchlist

## User Journey Overview

Thesis Watchlist strictly structures user interaction to prioritize investment context over raw numbers.

```
+--------------------------------------------------------------------------------+
| STEP 1: OPEN APPLICATION                                                       |
| Screen: THESIS WATCHLIST (Landing Summary)                                     |
| Content: Last Checked Date/Time, 3 Summary Counters, Glowing 'GO GROW' button |
| RULE: NO INDIVIDUAL STOCKS DISPLAYED ON THIS FIRST SCREEN                      |
+---------------------------------------+----------------------------------------+
                                        |
                                        v
+--------------------------------------------------------------------------------+
| STEP 2: USER CLICKS 'GO GROW'                                                  |
| Screen: MY WATCHLIST                                                           |
| Content: Stock Cards with real prices, daily %, and 3 status pills:            |
|          🟢 Thesis strengthening                                               |
|          🟠 Thesis needs attention                                             |
|          ⚪ No meaningful change                                               |
+---------------------------------------+----------------------------------------+
                                        |
        +-------------------------------+-------------------------------+
        |                                                               |
        v                                                               v
+-------------------------------+             +----------------------------------+
| STEP 3A: ADD STOCK            |             | STEP 3B: SELECT EXISTING STOCK   |
| 1. Click '+ ADD'              |             | Click stock card (e.g. Reliance) |
| 2. Search real company        |             +-----------------+----------------+
| 3. Select company             |                               |
| 4. Select category (Growth...) |                              v
| 5. Enter thesis in own words  |             +----------------------------------+
| 6. System interprets thesis   |             | STEP 4: COMPANY PAGE             |
| 7. Initial evaluation runs    |             | Default Tab: THESIS              |
+---------------+---------------+             | Content: Your Thesis, Status,    |
                |                             | Current Evidence (↑ 8%), Context |
                +---------------------------->| Action: Click 'SEE WHAT CHANGED' |
                                              +-----------------+----------------+
                                                                |
                                                                v
                                              +----------------------------------+
                                              | STEP 5: WHAT CHANGED?            |
                                              | Core Product Page                |
                                              | Sections:                        |
                                              | 1. SUPPORTING YOUR THESIS        |
                                              | 2. WORKING AGAINST YOUR THESIS   |
                                              | 3. NEUTRAL / OTHER RELEVANT      |
                                              | 4. Bottom Diagnostic Diagnosis   |
                                              |    Full Explainability Reason    |
                                              +-----------------+----------------+
                                                                |
                                                                v
                                              +----------------------------------+
                                              | STEP 6: RETURN TO HOME SUMMARY   |
                                              | Landing counters updated with    |
                                              | latest evaluation results        |
                                              +----------------------------------+
```

---

## Screen-by-Screen Breakdown

### 1. Landing Summary (Screen 1)
- **Header**: `THESIS WATCHLIST`
- **Subheader**: `Your watchlist, with context.`
- **Context**: `LAST CHECKED: [timestamp]`
- **Three Metric Boxes**:
  - `THESIS CHANGED` (Stocks whose underlying thesis signals shifted)
  - `NEEDS ATTENTION` (Stocks with contradicting real-world signals)
  - `NO CHANGE` (Stocks with stable baselines)
- **Primary CTA**: `GO GROW →`
- **Strict Constraint**: Under no circumstances are individual stock tickers, prices, or cards shown on this screen.

### 2. My Watchlist (Screen 2)
- Reached exclusively by clicking `GO GROW` or `#nav-brand-link`.
- Displays real equity listings:
  - Company Full Name
  - Ticker Symbol (e.g., `RELIANCE`, `TATAMOTORS`, `INFY`)
  - Live/Delayed market price with currency symbol (₹)
  - Daily percentage variance (+/- %)
  - Thesis Status Pill:
    - 🟢 `Thesis strengthening`
    - 🟠 `Thesis needs attention`
    - ⚪ `No meaningful change`
- Controls:
  - Real-time client-side search input filter.
  - `+ ADD` button to trigger company ingestion.
  - `🔄 Re-evaluate` button to batch trigger background evaluations.

### 3. Add Stock & Thesis Structuring Modal (Screen 3)
1. **Search Interface**: Real autocomplete querying exchange symbols and corporate names.
2. **Category Selection**:
   - ○ Growth
   - ○ Valuation
   - ○ Business performance
   - ○ Risk
   - ○ Event
   - ○ Price
   - ○ Industry / sector
   - ○ Other
3. **Thesis Input**: Textarea for free-form rationale (e.g. *"I think Jio growth and 5G tariff hikes will improve digital operating margins"*).
4. **Processing Pipeline**:
   - Backend Thesis Interpreter extracts entities and determines target metrics.
   - Initial quote, fundamentals, and news are fetched from live feeds.
   - Initial baseline snapshot is recorded.
   - Immediate navigation to the Company page.

### 4. Company Detail Hub (Screen 4)
- **Header**: Real-time price, day change, data freshness badge (`LIVE` / `DELAYED`), and thesis status badge.
- **Tabs**:
  1. **THESIS (Selected by default)**:
     - Prominent quote banner with user's exact thesis and category.
     - "CURRENT EVIDENCE" grid displaying real signals with directional arrows (`↑ 8%`, `↓ 2.1%`).
     - Alert line: *"Since your last check: X relevant signals changed."*
     - Button: `SEE WHAT CHANGED →`
  2. **OVERVIEW**:
     - Key financial stats (Today's High/Low, 52W High/Low, Market Cap, Volume, P/E, Market Status).
     - Interactive Price Chart with range intervals: `1D`, `1W`, `1M`, `6M`, `1Y`, `5Y`, `ALL`.
  3. **FUNDAMENTALS**:
     - Complete ratio grid (P/E, P/B, EPS, ROE, ROCE, Div Yield, Revenue, Profit, Margins, Debt, FCF, EBITDA).
     - "Not available" shown cleanly for missing provider fields.
     - Quarterly financial history table.
  4. **NEWS**:
     - `RELEVANT TO YOUR THESIS` (Ranked by semantic match, with thesis relevance justification and classification).
     - `ALL COMPANY NEWS` (General press coverage).
  5. **TECHNICALS**:
     - 14-period RSI, MACD with signal line and histogram, Moving Averages (SMA20, SMA50, SMA200), Annualized Volatility, and Trend indicator (`BULLISH`, `BEARISH`, `NEUTRAL`).

### 5. What Changed? (Screen 5 — Core Intelligence)
- Displays user thesis prominently.
- Three dedicated evidence panels:
  - **SUPPORTING YOUR THESIS**: Cards featuring signal name, baseline vs current value, `✓ Supports your thesis`, diagnostic rationale, source, and confidence score.
  - **WORKING AGAINST YOUR THESIS**: Cards featuring signal name, variance, `⚠ Works against your thesis`, and cautionary context.
  - **NEUTRAL / OTHER RELEVANT CHANGES**: Contextual movements within normal trading baselines.
- **Diagnostic Status Synthesis**:
  - Status pill (e.g. 🟠 `NEEDS ATTENTION`).
  - Clear count comparison: *"2 signals support your thesis • 2 signals work against it"*.
  - Explainability sentence: *"Your thesis needs attention because 2 relevant signals strengthened while 2 relevant signals weakened"*.
  - Button to re-evaluate on demand with live market data.
