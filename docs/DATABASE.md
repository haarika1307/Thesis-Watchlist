# Database Schema & Models — Thesis Watchlist

## Database Overview

Thesis Watchlist utilizes SQLAlchemy ORM with support for PostgreSQL in production/containerized environments and SQLite for immediate local execution. Schema versions are managed through Alembic migrations.

---

## Entity Relationship Diagram

```
+-------------------+             +-----------------------+
|       User        | 1         * |       Watchlist       |
| id (PK)           +-------------> id (PK)               |
| name              |             | userId (FK)           |
| email (Unique)    |             | name                  |
| hashed_password   |             | createdAt, updatedAt  |
+---------+---------+             +-----------+-----------+
          | 1                                 | 1
          |                                   |
          | *                                 | *
+---------v---------+             +-----------v-----------+
|      Thesis       | 1         1 |     WatchlistItem     |
| id (PK)           |<------------+ id (PK)               |
| userId (FK)       |             | watchlistId (FK)      |
| watchlistItemId   |             | symbol (Indexed)      |
| text, category    |             | companyName, exchange |
| status            |             +-----------------------+
| lastEvaluatedAt   |               Unique: (watchlistId, symbol)
+---+---+---+---+---+
    |   |   |   |
 1  |   |   |   |  1
    |   |   |   +--------------------------+
 *  |   |   | *                            | *
+---v---+   |  +--------------------+  +---v------------------+
| Thesis|   |  |     Evaluation     |  |    NewsRelevance     |
| Signal|   |  | id (PK)            |  | id (PK)              |
| id(PK)|   |  | thesisId (FK)      |  | newsArticleId (FK)   |
| topic |   |  | status, counts     |  | thesisId (FK)        |
| dir   |   |  | summary, timestamp |  | score, classification|
+-------+   |  +--------------------+  +----------------------+
            | 1
            |
            | *
        +---v----------------+
        |      Evidence      |
        | id (PK)            |
        | thesisId (FK)      |
        | symbol, signalName |
        | current/prev value |
        | classification     |
        | explanation        |
        +--------------------+

Historical Snapshot Models (Decoupled Time-Series):
+-----------------------+     +--------------------------+
|    MarketSnapshot     |     |   FundamentalSnapshot    |
| id (PK)               |     | id (PK)                  |
| symbol (Indexed)      |     | symbol (Indexed)         |
| price, volume, pct    |     | pe, pb, eps, roe, roce   |
| timestamp (Indexed)   |     | revenue, margin, debt    |
+-----------------------+     | timestamp (Indexed)      |
                              +--------------------------+
```

---

## Tables & Fields Specification

### 1. `users`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY | UUID string |
| `name` | VARCHAR(100) | NOT NULL | User display name |
| `email` | VARCHAR(255) | UNIQUE, INDEX, NOT NULL | Account email address |
| `hashed_password` | VARCHAR(255) | NOT NULL | Bcrypt password hash |
| `createdAt` | DATETIME | NOT NULL | Account creation timestamp |
| `updatedAt` | DATETIME | NOT NULL | Last account update timestamp |

### 2. `watchlists`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY | UUID string |
| `userId` | VARCHAR(36) | FK (`users.id`), INDEX, NOT NULL | Owning user |
| `name` | VARCHAR(150) | NOT NULL | Watchlist title |
| `createdAt` | DATETIME | NOT NULL | Creation timestamp |
| `updatedAt` | DATETIME | NOT NULL | Last update timestamp |

### 3. `watchlist_items`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY | UUID string |
| `watchlistId` | VARCHAR(36) | FK (`watchlists.id`), INDEX, NOT NULL | Parent watchlist |
| `symbol` | VARCHAR(50) | INDEX, NOT NULL | Exchange ticker symbol |
| `companyName` | VARCHAR(200) | NOT NULL | Full entity legal name |
| `exchange` | VARCHAR(20) | NOT NULL | Market exchange (NSE, BSE, NASDAQ) |
| `createdAt` | DATETIME | NOT NULL | Creation timestamp |
| `updatedAt` | DATETIME | NOT NULL | Update timestamp |
- **Unique Constraint**: `uq_watchlist_symbol` on `(watchlistId, symbol)`.

### 4. `theses`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY | UUID string |
| `userId` | VARCHAR(36) | FK (`users.id`), INDEX, NOT NULL | Authoring user |
| `watchlistItemId` | VARCHAR(36) | FK (`watchlist_items.id`), UNIQUE, INDEX, NOT NULL | Monitored stock item |
| `text` | TEXT | NOT NULL | Free-form thesis explanation |
| `category` | VARCHAR(50) | NOT NULL | Growth, Valuation, Turnaround, Risk, etc. |
| `status` | VARCHAR(50) | NOT NULL | `STRENGTHENING`, `NEEDS_ATTENTION`, `NO_CHANGE` |
| `createdAt` | DATETIME | NOT NULL | Creation timestamp |
| `updatedAt` | DATETIME | NOT NULL | Update timestamp |
| `lastEvaluatedAt` | DATETIME | NULLABLE | Timestamp of last evaluation execution |

### 5. `thesis_signals`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY | UUID string |
| `thesisId` | VARCHAR(36) | FK (`theses.id`), INDEX, NOT NULL | Parent thesis |
| `topic` | VARCHAR(100) | NOT NULL | Financial metric topic / domain |
| `signalName` | VARCHAR(150) | NOT NULL | Name of metric to monitor |
| `description` | TEXT | NULLABLE | Signal operational description |
| `direction` | VARCHAR(20) | NOT NULL | `POSITIVE`, `NEGATIVE`, `NEUTRAL` |
| `importance` | VARCHAR(20) | NOT NULL | `HIGH`, `MEDIUM`, `LOW` |
| `currentValue` | VARCHAR(255) | NULLABLE | Latest observed value string |
| `previousValue` | VARCHAR(255) | NULLABLE | Previous observed baseline |
| `createdAt` | DATETIME | NOT NULL | Creation timestamp |
| `updatedAt` | DATETIME | NOT NULL | Update timestamp |

### 6. `market_snapshots`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY | UUID string |
| `symbol` | VARCHAR(50) | INDEX, NOT NULL | Exchange ticker symbol |
| `price` | FLOAT | NOT NULL | Traded market price |
| `percentageChange` | FLOAT | NULLABLE | Day variance percentage |
| `volume` | BIGINT | NULLABLE | Total volume traded |
| `volatility` | FLOAT | NULLABLE | 20-day annualized historical volatility |
| `marketCap` | FLOAT | NULLABLE | Market capitalization |
| `timestamp` | DATETIME | INDEX, NOT NULL | Snapshot observation timestamp |

### 7. `fundamental_snapshots`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY | UUID string |
| `symbol` | VARCHAR(50) | INDEX, NOT NULL | Exchange ticker symbol |
| `pe` | FLOAT | NULLABLE | Trailing/Forward Price-to-Earnings |
| `pb` | FLOAT | NULLABLE | Price-to-Book |
| `eps` | FLOAT | NULLABLE | Earnings per share |
| `roe` | FLOAT | NULLABLE | Return on Equity (%) |
| `roce` | FLOAT | NULLABLE | Return on Capital Employed (%) |
| `revenue` | FLOAT | NULLABLE | Top-line revenue |
| `profit` | FLOAT | NULLABLE | Net profit after tax |
| `ebitda` | FLOAT | NULLABLE | Operating cash profit |
| `margin` | FLOAT | NULLABLE | Operating margin percentage |
| `debt` | FLOAT | NULLABLE | Total balance sheet debt |
| `freeCashFlow` | FLOAT | NULLABLE | Trailing Free Cash Flow |
| `timestamp` | DATETIME | INDEX, NOT NULL | Snapshot timestamp |

### 8. `evidence`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY | UUID string |
| `thesisId` | VARCHAR(36) | FK (`theses.id`), INDEX, NOT NULL | Evaluated thesis |
| `symbol` | VARCHAR(50) | INDEX, NOT NULL | Stock symbol |
| `signalName` | VARCHAR(150) | NOT NULL | Evaluated signal |
| `sourceType` | VARCHAR(50) | NOT NULL | `FUNDAMENTAL`, `MARKET`, `NEWS` |
| `sourceId` | VARCHAR(100) | NULLABLE | Source document or quote ID |
| `previousValue` | VARCHAR(255) | NULLABLE | Baseline value |
| `currentValue` | VARCHAR(255) | NULLABLE | Observed current value |
| `changeValue` | VARCHAR(255) | NULLABLE | Delta representation |
| `changePercentage` | FLOAT | NULLABLE | Numerical percentage delta |
| `classification` | VARCHAR(20) | NOT NULL | `SUPPORTING`, `CONTRADICTING`, `NEUTRAL` |
| `confidence` | FLOAT | NOT NULL | Confidence score (0.0 to 1.0) |
| `explanation` | TEXT | NOT NULL | Human-readable diagnosis |
| `timestamp` | DATETIME | INDEX, NOT NULL | Evidence evaluation timestamp |

### 9. `evaluations`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY | UUID string |
| `thesisId` | VARCHAR(36) | FK (`theses.id`), INDEX, NOT NULL | Evaluated thesis |
| `status` | VARCHAR(50) | NOT NULL | Result status |
| `supportingCount` | INTEGER | NOT NULL | Number of supporting signals |
| `contradictingCount`| INTEGER | NOT NULL | Number of contradicting signals |
| `neutralCount` | INTEGER | NOT NULL | Number of neutral signals |
| `confidence` | FLOAT | NOT NULL | Synthesis confidence |
| `summary` | TEXT | NOT NULL | Explainability summary statement |
| `evaluatedAt` | DATETIME | INDEX, NOT NULL | Evaluation timestamp |

### 10. `watchlist_evaluations`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | VARCHAR(36) | PRIMARY KEY | UUID string |
| `watchlistId` | VARCHAR(36) | FK (`watchlists.id`), INDEX, NOT NULL | Evaluated watchlist |
| `lastCheckedAt` | DATETIME | NOT NULL | Aggregation timestamp |
| `thesisChangedCount`| INTEGER | NOT NULL | Changed thesis count |
| `needsAttentionCount`| INTEGER | NOT NULL | Needs attention count |
| `noChangeCount` | INTEGER | NOT NULL | Stable count |

### 11. `news_articles` & 12. `news_relevance`
Stores ingested articles and links them to evaluated theses with relevance scores and sentiment classifications.
