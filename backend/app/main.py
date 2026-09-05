import os
import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from backend.app.core.config import settings
from backend.app.db.database import init_db, SessionLocal
from backend.app.api.health import router as health_router
from backend.app.api.auth import router as auth_router, get_or_create_default_user
from backend.app.api.stocks import router as stocks_router
from backend.app.api.watchlists import router as watchlists_router
from backend.app.api.theses import router as theses_router
from backend.app.api.summary import router as summary_router
from backend.app.api.ws import router as ws_router
from backend.app.workers.market_updates import market_stream_manager
from backend.app.models.user import User
from backend.app.models.watchlist import Watchlist
from backend.app.models.watchlist_item import WatchlistItem
from backend.app.models.thesis import Thesis
from backend.app.models.thesis_signal import ThesisSignal
from backend.app.services.thesis.interpreter import thesis_interpreter
from backend.app.services.market_data.provider_factory import get_market_data_provider
from backend.app.services.news.news_service import news_service
from backend.app.services.evaluation.evaluator import thesis_evaluator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("smart_watchlist")

def seed_initial_data():
    """Seed initial watchlist items with real theses if the database is empty."""
    db = SessionLocal()
    try:
        user = get_or_create_default_user(db)
        wl = db.query(Watchlist).filter(Watchlist.userId == user.id).first()
        if not wl:
            wl = Watchlist(userId=user.id, name="My Growth Watchlist")
            db.add(wl)
            db.commit()
            db.refresh(wl)

        existing_count = db.query(WatchlistItem).filter(WatchlistItem.watchlistId == wl.id).count()
        if existing_count == 0:
            logger.info("Seeding real initial stocks and theses...")
            initial_stocks = [
                {
                    "symbol": "RELIANCE.NS",
                    "companyName": "Reliance Industries Limited",
                    "exchange": "NSE",
                    "category": "Growth",
                    "thesis": "I think Jio growth and 5G tariff hikes will continue to improve Reliance's digital revenue and operating performance."
                },
                {
                    "symbol": "TATAMOTORS.NS",
                    "companyName": "Tata Motors Limited",
                    "exchange": "NSE",
                    "category": "Turnaround",
                    "thesis": "EV adoption and market share expansion in passenger vehicles combined with JLR debt reduction will strengthen profitability."
                },
                {
                    "symbol": "INFY.NS",
                    "companyName": "Infosys Limited",
                    "exchange": "NSE",
                    "category": "Industry / sector",
                    "thesis": "I think IT demand will recover as client discretionary spend and large digital transformation deal wins pick up."
                }
            ]

            for s in initial_stocks:
                try:
                    item = WatchlistItem(
                        watchlistId=wl.id,
                        symbol=s["symbol"],
                        companyName=s["companyName"],
                        exchange=s["exchange"]
                    )
                    db.add(item)
                    db.commit()
                    db.refresh(item)

                    profile = thesis_interpreter.interpret(s["thesis"], s["category"], s["companyName"])
                    thesis = Thesis(
                        userId=user.id,
                        watchlistItemId=item.id,
                        text=s["thesis"],
                        category=s["category"],
                        status="NO_CHANGE"
                    )
                    db.add(thesis)
                    db.commit()
                    db.refresh(thesis)

                    for sig in profile.signals:
                        db_sig = ThesisSignal(
                            thesisId=thesis.id,
                            topic=sig.topic,
                            signalName=sig.signalName,
                            description=sig.targetMetric or sig.description,
                            direction=sig.direction,
                            importance=sig.importance
                        )
                        db.add(db_sig)
                    db.commit()
                except Exception as e:
                    logger.warning(f"Error seeding stock {s['symbol']}: {e}")
                    db.rollback()

            logger.info("Initial seed stocks recorded. Running background live evaluation...")
    except Exception as e:
        logger.error(f"Error during data seeding: {e}")
    finally:
        db.close()

def run_seed_evaluations_background():
    """Background evaluation runner for seed stocks."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "investor@smartwatchlist.com").first()
        if not user:
            return
        wl = db.query(Watchlist).filter(Watchlist.userId == user.id).first()
        if not wl:
            return

        provider = get_market_data_provider()
        for item in wl.items:
            if item.thesis:
                try:
                    quote = provider.get_quote(item.symbol)
                    fund = provider.get_fundamentals(item.symbol)
                    tech = provider.get_technicals(item.symbol)
                    news = news_service.get_ranked_news_for_thesis(
                        item.symbol,
                        item.companyName,
                        item.thesis.text,
                        [{"signalName": sig_def.signalName, "topic": sig_def.topic, "description": sig_def.description} for sig_def in item.thesis.signals]
                    )
                    thesis_evaluator.evaluate_thesis(db, item.thesis, quote, fund, tech, news)
                except Exception as e:
                    logger.warning(f"Could not run live evaluation for {item.symbol}: {e}")
        thesis_evaluator.evaluate_watchlist(db, wl.id)
        logger.info("Initial live evaluations completed.")
    except Exception as e:
        logger.error(f"Background evaluation error: {e}")
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Thesis Watchlist application...")
    init_db()
    seed_initial_data()
    # Run seed evaluations in background thread so server starts instantly
    import threading
    threading.Thread(target=run_seed_evaluations_background, daemon=True).start()
    # Start WebSocket background streaming task
    stream_task = asyncio.create_task(market_stream_manager.start_background_stream())
    yield
    # Shutdown
    market_stream_manager._is_running = False
    stream_task.cancel()
    logger.info("Shutdown complete.")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Thesis Watchlist — A Thesis-First Stock Intelligence Platform",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers under /api
app.include_router(health_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(stocks_router, prefix="/api")
app.include_router(watchlists_router, prefix="/api")
app.include_router(theses_router, prefix="/api")
app.include_router(summary_router, prefix="/api")
app.include_router(ws_router, prefix="/api")

# Serve Frontend static assets
frontend_path = Path(__file__).resolve().parents[2] / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")

@app.get("/")
def serve_index():
    """Serve single-page frontend application."""
    index_file = frontend_path / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return JSONResponse({"message": "Thesis Watchlist API is running. Frontend not found."})

@app.get("/{full_path:path}")
def serve_spa_routes(full_path: str):
    """Fallback handler for SPA routing."""
    # If path exists in static frontend directory, return it
    target = frontend_path / full_path
    if target.exists() and target.is_file():
        return FileResponse(str(target))
    # Otherwise return index.html for client-side routing
    index_file = frontend_path / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return JSONResponse({"message": f"Route /{full_path} not found"}, status_code=404)
