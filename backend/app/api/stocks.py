from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.schemas.market import (
    StockSearchResult,
    QuoteResponse,
    HistoryResponse,
    FundamentalsResponse,
    TechnicalsResponse
)
from backend.app.schemas.news import NewsListResponse
from backend.app.services.market_data.provider_factory import get_market_data_provider
from backend.app.services.news.news_service import news_service
from backend.app.models.watchlist_item import WatchlistItem
from backend.app.models.thesis import Thesis
from backend.app.api.auth import get_current_user
from backend.app.models.user import User

router = APIRouter(prefix="/stocks", tags=["Stocks & Market Data"])

@router.get("/search", response_model=List[StockSearchResult])
def search_stocks(q: str = Query(..., min_length=1, description="Query string to search companies")):
    """Search for real listed companies across exchanges."""
    provider = get_market_data_provider()
    return provider.search(q)

@router.get("/{symbol}", response_model=QuoteResponse)
def get_quote(symbol: str):
    """Get real-time / latest quote for a stock."""
    provider = get_market_data_provider()
    quote = provider.get_quote(symbol)
    if not quote or quote.price == 0.0:
        # Check if symbol exists with or without .NS
        pass
    return quote

@router.get("/{symbol}/history", response_model=HistoryResponse)
def get_history(symbol: str, range: str = Query("1M", description="1D, 1W, 1M, 6M, 1Y, 5Y, ALL")):
    """Get real historical OHLCV candles."""
    provider = get_market_data_provider()
    return provider.get_history(symbol, range)

@router.get("/{symbol}/fundamentals", response_model=FundamentalsResponse)
def get_fundamentals(symbol: str):
    """Get real quarterly and annual fundamentals, ratios, and balance sheet metrics."""
    provider = get_market_data_provider()
    return provider.get_fundamentals(symbol)

@router.get("/{symbol}/technicals", response_model=TechnicalsResponse)
def get_technicals(symbol: str):
    """Get real computed technical indicators (RSI, MACD, SMAs, Volatility)."""
    provider = get_market_data_provider()
    return provider.get_technicals(symbol)

@router.get("/{symbol}/news", response_model=NewsListResponse)
def get_stock_news(
    symbol: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get real company news partitioned into RELEVANT TO THESIS and ALL COMPANY NEWS."""
    provider = get_market_data_provider()
    quote = provider.get_quote(symbol)
    company_name = quote.companyName if quote else ""

    # Check if user has an active thesis for this stock
    item = db.query(WatchlistItem)\
        .join(Thesis, Thesis.watchlistItemId == WatchlistItem.id)\
        .filter(WatchlistItem.symbol == symbol, Thesis.userId == current_user.id)\
        .first()

    thesis_text = item.thesis.text if (item and item.thesis) else ""
    signals = []
    if item and item.thesis:
        signals = [
            {"signalName": s.signalName, "topic": s.topic, "description": s.description}
            for s in item.thesis.signals
        ]

    return news_service.get_ranked_news_for_thesis(symbol, company_name, thesis_text, signals)
