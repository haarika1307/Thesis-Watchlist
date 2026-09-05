import logging
from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.models.user import User
from backend.app.models.watchlist_item import WatchlistItem
from backend.app.models.thesis import Thesis
from backend.app.models.thesis_signal import ThesisSignal
from backend.app.schemas.thesis import (
    ThesisResponse,
    ThesisCreate,
    ThesisUpdate,
    ThesisSignalResponse
)
from backend.app.schemas.evidence import WhatChangedResponse, EvidenceResponse
from backend.app.services.market_data.provider_factory import get_market_data_provider
from backend.app.services.news.news_service import news_service
from backend.app.services.evaluation.evaluator import thesis_evaluator
from backend.app.services.thesis.interpreter import thesis_interpreter
from backend.app.api.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/thesis", tags=["Thesis Intelligence"])

def _get_thesis_for_symbol(db: Session, user_id: str, symbol: str) -> Thesis:
    """Helper to locate user's thesis for a symbol."""
    item = db.query(WatchlistItem)\
        .join(Thesis, Thesis.watchlistItemId == WatchlistItem.id)\
        .filter(WatchlistItem.symbol == symbol, Thesis.userId == user_id)\
        .first()

    if not item or not item.thesis:
        # Fallback: check without suffix or case-insensitive
        sym_clean = symbol.split(".")[0].upper()
        item = db.query(WatchlistItem)\
            .join(Thesis, Thesis.watchlistItemId == WatchlistItem.id)\
            .filter(WatchlistItem.symbol.ilike(f"%{sym_clean}%"), Thesis.userId == user_id)\
            .first()

    if not item or not item.thesis:
        raise HTTPException(status_code=404, detail=f"No active thesis found for symbol {symbol}")

    return item.thesis

@router.get("/{symbol}", response_model=ThesisResponse)
def get_thesis(
    symbol: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve user thesis for a stock."""
    th = _get_thesis_for_symbol(db, current_user.id, symbol)
    return ThesisResponse(
        id=th.id,
        userId=th.userId,
        watchlistItemId=th.watchlistItemId,
        text=th.text,
        category=th.category,
        status=th.status,
        createdAt=th.createdAt,
        updatedAt=th.updatedAt,
        lastEvaluatedAt=th.lastEvaluatedAt,
        signals=[ThesisSignalResponse.model_validate(s) for s in th.signals]
    )

@router.put("/{symbol}", response_model=ThesisResponse)
def update_thesis(
    symbol: str,
    th_in: ThesisUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update thesis text or category and re-derive signals."""
    th = _get_thesis_for_symbol(db, current_user.id, symbol)
    if th_in.text:
        th.text = th_in.text
    if th_in.category:
        th.category = th_in.category

    # Re-derive signals if text changed
    if th_in.text or th_in.category:
        profile = thesis_interpreter.interpret(th.text, th.category, th.watchlist_item.companyName)
        # Clear existing signals
        db.query(ThesisSignal).filter(ThesisSignal.thesisId == th.id).delete()
        for sig in profile.signals:
            db_sig = ThesisSignal(
                thesisId=th.id,
                topic=sig.topic,
                signalName=sig.signalName,
                description=sig.targetMetric or sig.description,
                direction=sig.direction,
                importance=sig.importance
            )
            db.add(db_sig)

    th.updatedAt = datetime.now(timezone.utc)
    db.commit()
    db.refresh(th)

    return ThesisResponse(
        id=th.id,
        userId=th.userId,
        watchlistItemId=th.watchlistItemId,
        text=th.text,
        category=th.category,
        status=th.status,
        createdAt=th.createdAt,
        updatedAt=th.updatedAt,
        lastEvaluatedAt=th.lastEvaluatedAt,
        signals=[ThesisSignalResponse.model_validate(s) for s in th.signals]
    )

@router.get("/{symbol}/signals", response_model=List[ThesisSignalResponse])
def get_thesis_signals(
    symbol: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get active signals monitored for this thesis."""
    th = _get_thesis_for_symbol(db, current_user.id, symbol)
    return [ThesisSignalResponse.model_validate(s) for s in th.signals]

@router.get("/{symbol}/changes", response_model=WhatChangedResponse)
def get_what_changed(
    symbol: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve detailed 'What Changed' breakdown separating supporting, contradicting, and neutral evidence."""
    th = _get_thesis_for_symbol(db, current_user.id, symbol)
    provider = get_market_data_provider()

    quote = provider.get_quote(th.watchlist_item.symbol)
    fund = provider.get_fundamentals(th.watchlist_item.symbol)
    tech = provider.get_technicals(th.watchlist_item.symbol)
    news = news_service.get_ranked_news_for_thesis(
        th.watchlist_item.symbol,
        th.watchlist_item.companyName,
        th.text,
        [{"signalName": s.signalName, "topic": s.topic, "description": s.description} for s in th.signals]
    )

    # Run evaluation
    return thesis_evaluator.evaluate_thesis(db, th, quote, fund, tech, news)

@router.post("/{symbol}/evaluate", response_model=WhatChangedResponse)
def run_thesis_evaluation(
    symbol: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Run an on-demand re-evaluation of thesis."""
    return get_what_changed(symbol, db, current_user)
