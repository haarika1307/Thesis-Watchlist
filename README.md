# Smart Watchlist — Thesis-First Stock Intelligence Platform

Smart Watchlist is a full-stack, thesis-first investment intelligence platform that tracks **why** you are watching a stock, monitors real-world fundamental and price changes, and classifies supporting versus contradicting evidence.

---

## The Core Product Loop

Traditional watchlists tell users: *"What stocks am I watching?"*

Smart Watchlist answers:
**"Why am I watching this stock, what has changed since I last checked, and does that change support or contradict the reason I was watching it?"**

```
ADD STOCK
   ↓
EXPLAIN WHY (THESIS)
   ↓
STRUCTURE THE THESIS
   ↓
TRACK RELEVANT REAL-WORLD SIGNALS
   ↓
DETECT MEANINGFUL CHANGES
   ↓
COMPARE CHANGES AGAINST THESIS
   ↓
EXPLAIN SUPPORTING / CONTRADICTING EVIDENCE
   ↓
USER REVIEWS WHAT CHANGED
```

---

## Key Features

- **Summary-First Landing Page**: Displays watchlist health counters (`THESIS CHANGED`, `NEEDS ATTENTION`, `NO CHANGE`) with zero ticker clutter until you click `GO GROW →`.
- **Thesis Structuring Engine**: Converts free-form natural language investment rationales into structured signal profiles with directional targets.
- **Change Detection with Significance Logic**: Filters out routine market noise and detects high-impact variances across price swings, quarterly margins, top-line growth, and corporate deal announcements.
- **Evidence Classification**: Explicitly categorizes observations into **Supporting your thesis** and **Working against your thesis**, accompanied by an explainability diagnosis.
- **Real Market & News Data**: Ingests real quotes, historical candles, SEC/MCA fundamental metrics, and news articles (Yahoo Finance API & Google News RSS). Zero fake, mock, or placeholder data.
- **Modern Dark UI**: Pure HTML5, CSS3, and Vanilla JavaScript with custom HTML5 Canvas financial charts, status pills, and WebSocket live updates.

---

## Quick Start

### 1. Prerequisites
- Python 3.10+
- (Optional) Docker & Docker Compose for PostgreSQL

### 2. Run Locally

```bash
# Clone and enter directory
cd Smart-Grow-Watchlist

# Create virtual environment and install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start application server
./venv/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

Open your browser at **[http://localhost:8000](http://localhost:8000)**.

### 3. Run with Docker Compose

```bash
docker-compose up --build -d
```

Access the application at **[http://localhost:8000](http://localhost:8000)**.

---

## Project Structure

```
Smart-Grow-Watchlist/
├── backend/
│   ├── alembic/                # Alembic database migrations
│   ├── app/
│   │   ├── api/                # REST & WebSocket endpoints
│   │   ├── core/               # Configuration & security (JWT, bcrypt)
│   │   ├── db/                 # Database engine & session management
│   │   ├── models/             # 12 SQLAlchemy ORM models
│   │   ├── schemas/            # Pydantic validation schemas
│   │   ├── services/
│   │   │   ├── market_data/    # Real market provider abstraction & caching
│   │   │   ├── news/           # Real company news provider & ranking
│   │   │   ├── thesis/         # Thesis NLP & semantic interpreter
│   │   │   ├── change_detection/ # Significance filtering engine
│   │   │   ├── intelligence/   # Evidence classifier (Supporting/Contradicting)
│   │   │   ├── evaluation/     # Status synthesis & explainability
│   │   │   └── snapshot/       # Time-series baseline state capture
│   │   └── workers/            # WebSocket live market streaming manager
│   └── main.py                 # FastAPI application root & SPA mounting
├── frontend/
│   ├── css/                    # Custom CSS design system & pages
│   ├── js/                     # Modular Vanilla JavaScript controllers
│   └── index.html              # Single Page Application
├── docs/                       # Comprehensive documentation
│   ├── ARCHITECTURE.md
│   ├── PRODUCT_FLOW.md
│   ├── API.md
│   ├── DATABASE.md
│   └── WALKTHROUGH.md
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env.example
```

---

## Documentation

Detailed design documents are available in the [`docs/`](file:///Users/gautham/Documents/Smart-Grow-Watchlist/docs) directory:
- [System Architecture](file:///Users/gautham/Documents/Smart-Grow-Watchlist/docs/ARCHITECTURE.md)
- [Product Journey & Screens](file:///Users/gautham/Documents/Smart-Grow-Watchlist/docs/PRODUCT_FLOW.md)
- [REST & WebSocket API Reference](file:///Users/gautham/Documents/Smart-Grow-Watchlist/docs/API.md)
- [Database Schema & Models](file:///Users/gautham/Documents/Smart-Grow-Watchlist/docs/DATABASE.md)
- [System Walkthrough & Verification Guide](file:///Users/gautham/Documents/Smart-Grow-Watchlist/docs/WALKTHROUGH.md)
