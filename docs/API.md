# API Specification — Thesis Watchlist

Base URL: `http://localhost:8000/api`

## Endpoints Overview

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | System health check and provider status |
| `POST` | `/auth/register` | Register new user account |
| `POST` | `/auth/login` | Login and receive JWT access token |
| `GET` | `/auth/me` | Retrieve authenticated user profile |
| `GET` | `/watchlist/summary` | Retrieve Landing Page summary counters |
| `POST` | `/evaluations/run` | Batch execute thesis evaluations across all items |
| `GET` | `/watchlists` | Get user watchlists with items and live quotes |
| `POST` | `/watchlists` | Create a new watchlist |
| `GET` | `/watchlists/{id}` | Get single watchlist detail |
| `POST` | `/watchlists/{id}/items` | Add stock + thesis to watchlist |
| `DELETE` | `/watchlists/{id}/items/{symbol}` | Remove stock from watchlist |
| `GET` | `/stocks/search?q={query}` | Autocomplete search for real listed companies |
| `GET` | `/stocks/{symbol}` | Real-time / delayed stock quote |
| `GET` | `/stocks/{symbol}/history?range={range}` | Historical OHLCV candles (1D, 1W, 1M, 6M, 1Y, 5Y, ALL) |
| `GET` | `/stocks/{symbol}/fundamentals` | Quarterly/annual fundamentals and ratios |
| `GET` | `/stocks/{symbol}/technicals` | Computed technical indicators (RSI, MACD, SMAs) |
| `GET` | `/stocks/{symbol}/news` | Company news partitioned by thesis relevance |
| `GET` | `/thesis/{symbol}` | Retrieve active thesis for a stock |
| `PUT` | `/thesis/{symbol}` | Update thesis text or category |
| `GET` | `/thesis/{symbol}/signals` | Retrieve structured signals monitored |
| `GET` | `/thesis/{symbol}/changes` | Core "What Changed" evaluation breakdown |
| `POST` | `/thesis/{symbol}/evaluate` | Trigger immediate live re-evaluation |
| `WS` | `/ws/market` | WebSocket stream for live market quote subscriptions |

---

## Detailed Endpoint Specifications

### 1. Watchlist Summary (Landing View)
`GET /api/watchlist/summary`

#### Response `200 OK`
```json
{
  "watchlistId": "d981775f-2b15-46aa-83a3-b40ee5be39dc",
  "lastCheckedAt": "2026-09-05T08:12:00Z",
  "thesisChangedCount": 1,
  "needsAttentionCount": 2,
  "noChangeCount": 0,
  "totalStocks": 3
}
```

---

### 2. Add Stock With Thesis
`POST /api/watchlists/{watchlist_id}/items`

#### Request Body
```json
{
  "symbol": "RELIANCE.NS",
  "companyName": "Reliance Industries Limited",
  "exchange": "NSE",
  "category": "Growth",
  "thesisText": "I think Jio growth and 5G tariff hikes will continue to improve Reliance's digital revenue and operating performance."
}
```

#### Response `200 OK`
```json
{
  "id": "e42718ef-912b-4279-b1d7-2f1f31fbb891",
  "symbol": "RELIANCE.NS",
  "companyName": "Reliance Industries Limited",
  "exchange": "NSE",
  "price": 1322.0,
  "change": 9.2,
  "percentageChange": 0.7,
  "currency": "₹",
  "thesisStatus": "NEEDS_ATTENTION",
  "thesisText": "I think Jio growth and 5G tariff hikes will continue to improve Reliance's digital revenue and operating performance.",
  "thesisCategory": "Growth",
  "signalCount": 5,
  "supportingCount": 2,
  "contradictingCount": 1,
  "freshness": "DELAYED (15 min)",
  "lastEvaluatedAt": "2026-09-05T08:15:30Z"
}
```

---

### 3. What Changed? Evaluation
`GET /api/thesis/{symbol}/changes`

#### Response `200 OK`
```json
{
  "symbol": "RELIANCE.NS",
  "companyName": "Reliance Industries Limited",
  "thesisId": "c1f7db49-74d1-4171-be26-9f82d2f70359",
  "thesisText": "I think Jio growth and 5G tariff hikes will continue to improve Reliance's digital revenue and operating performance.",
  "thesisCategory": "Growth",
  "status": "NEEDS_ATTENTION",
  "supportingCount": 2,
  "contradictingCount": 1,
  "neutralCount": 1,
  "summary": "Your thesis needs attention because 2 relevant signals strengthened while 1 relevant signal weakened.",
  "lastEvaluatedAt": "2026-09-05T08:15:30Z",
  "supportingEvidence": [
    {
      "id": "ev_1788600000000_revenueGrowth",
      "thesisId": "c1f7db49-74d1-4171-be26-9f82d2f70359",
      "symbol": "RELIANCE.NS",
      "signalName": "Revenue Growth",
      "sourceType": "FUNDAMENTAL",
      "sourceId": "quarterly_filing_revenue",
      "previousValue": "₹2,35,000 Cr",
      "currentValue": "₹2,58,027 Cr",
      "changeValue": "+9.8%",
      "changePercentage": 9.8,
      "classification": "SUPPORTING",
      "confidence": 0.88,
      "explanation": "Top-line revenue expanded by +9.8%, directly verifying business growth.",
      "timestamp": "2026-09-05T08:15:30Z"
    },
    {
      "id": "ev_1788600000000_priceChange",
      "thesisId": "c1f7db49-74d1-4171-be26-9f82d2f70359",
      "symbol": "RELIANCE.NS",
      "signalName": "Market Price & Trend Confirmation",
      "sourceType": "MARKET",
      "sourceId": "quote_RELIANCE.NS",
      "previousValue": "₹1,312.80",
      "currentValue": "₹1,322.00",
      "changeValue": "+9.20 (+0.70%)",
      "changePercentage": 0.7,
      "classification": "SUPPORTING",
      "confidence": 0.85,
      "explanation": "Price positive momentum (+0.7%) aligns with affirmative thesis outlook.",
      "timestamp": "2026-09-05T08:15:30Z"
    }
  ],
  "contradictingEvidence": [
    {
      "id": "ev_1788600000000_operatingMargin",
      "thesisId": "c1f7db49-74d1-4171-be26-9f82d2f70359",
      "symbol": "RELIANCE.NS",
      "signalName": "Operating Margin",
      "sourceType": "FUNDAMENTAL",
      "sourceId": "sec_filing_margin",
      "previousValue": "16.8%",
      "currentValue": "15.4%",
      "changeValue": "-1.40%",
      "changePercentage": -1.4,
      "classification": "CONTRADICTING",
      "confidence": 0.85,
      "explanation": "Operating margin contracted by 1.40%, indicating margin pressure or cost inflation.",
      "timestamp": "2026-09-05T08:15:30Z"
    }
  ],
  "neutralEvidence": [
    {
      "id": "ev_1788600000000_pe",
      "thesisId": "c1f7db49-74d1-4171-be26-9f82d2f70359",
      "symbol": "RELIANCE.NS",
      "signalName": "Price-to-Earnings (P/E)",
      "sourceType": "FUNDAMENTAL",
      "sourceId": "sec_filing_pe",
      "previousValue": "26.4x",
      "currentValue": "26.8x",
      "changeValue": "+0.4x",
      "changePercentage": 1.5,
      "classification": "NEUTRAL",
      "confidence": 0.85,
      "explanation": "P/E multiple at 26.8x aligns with average market pricing.",
      "timestamp": "2026-09-05T08:15:30Z"
    }
  ]
}
```

---

### 4. WebSocket Market Streaming
`WS /api/ws/market`

#### Client Subscription Message
```json
{
  "action": "subscribe",
  "symbols": ["RELIANCE.NS", "TATAMOTORS.NS", "INFY.NS"]
}
```

#### Server Broadcast Message
```json
{
  "type": "QUOTE_UPDATE",
  "symbol": "RELIANCE.NS",
  "data": {
    "price": 1322.0,
    "change": 9.2,
    "percentageChange": 0.7,
    "volume": 6428190,
    "currency": "₹",
    "freshness": "DELAYED (15 min)",
    "timestamp": "2026-09-05T08:15:45Z"
  }
}
```
