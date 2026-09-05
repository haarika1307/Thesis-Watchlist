import logging
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.models.user import User
from backend.app.models.watchlist import Watchlist
from backend.app.models.watchlist_item import WatchlistItem
from backend.app.models.thesis import Thesis
from backend.app.models.thesis_signal import ThesisSignal
from backend.app.schemas.watchlist import (
    WatchlistCreate,
    WatchlistResponse,
    WatchlistItemCreate,
    WatchlistItemResponse,
    WatchlistItemDetail
)
from backend.app.services.market_data.provider_factory import get_market_data_provider
from backend.app.services.thesis.interpreter import thesis_interpreter
from backend.app.services.evaluation.evaluator import thesis_evaluator
from backend.app.services.news.news_service import news_service
from backend.app.api.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/watchlists", tags=["Watchlists"])

@router.get("", response_model=List[WatchlistResponse])
def get_user_watchlists(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all watchlists for current user with live stock metrics."""
    watchlists = db.query(Watchlist).filter(Watchlist.userId == current_user.id).all()
    if not watchlists:
        # Create default watchlist if none exists
        default_wl = Watchlist(userId=current_user.id, name="My Watchlist")
        db.add(default_wl)
        db.commit()
        db.refresh(default_wl)
        watchlists = [default_wl]

    provider = get_market_data_provider()
    results: List[WatchlistResponse] = []

    for wl in watchlists:
        items_detail: List[WatchlistItemDetail] = []
        for item in wl.items:
            try:
                quote = provider.get_quote(item.symbol)
                price = quote.price
                change = quote.change
                pct = quote.percentageChange
                currency = quote.currency
                freshness = quote.freshness
            except Exception:
                price = None
                change = None
                pct = None
                currency = "₹"
                freshness = "UNAVAILABLE"

            th = item.thesis
            status_val = th.status if th else "NO_CHANGE"
            th_text = th.text if th else None
            th_cat = th.category if th else None
            th_evaluated = th.lastEvaluatedAt if th else None
            sig_count = len(th.signals) if (th and th.signals) else 0

            # Count evidence if evaluated
            sup_count = len([e for e in th.evidence if e.classification == "SUPPORTING"]) if (th and th.evidence) else 0
            con_count = len([e for e in th.evidence if e.classification == "CONTRADICTING"]) if (th and th.evidence) else 0

            items_detail.append(WatchlistItemDetail(
                id=item.id,
                symbol=item.symbol,
                companyName=item.companyName,
                exchange=item.exchange,
                price=price,
                change=change,
                percentageChange=pct,
                currency=currency,
                thesisStatus=status_val,
                thesisText=th_text,
                thesisCategory=th_cat,
                signalCount=sig_count,
                supportingCount=sup_count,
                contradictingCount=con_count,
                freshness=freshness,
                lastEvaluatedAt=th_evaluated
            ))

        results.append(WatchlistResponse(
            id=wl.id,
            userId=wl.userId,
            name=wl.name,
            createdAt=wl.createdAt,
            updatedAt=wl.updatedAt,
            items=items_detail
        ))

    return results

@router.post("", response_model=WatchlistResponse)
def create_watchlist(
    wl_in: WatchlistCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new watchlist."""
    wl = Watchlist(userId=current_user.id, name=wl_in.name)
    db.add(wl)
    db.commit()
    db.refresh(wl)
    return WatchlistResponse(
        id=wl.id,
        userId=wl.userId,
        name=wl.name,
        createdAt=wl.createdAt,
        updatedAt=wl.updatedAt,
        items=[]
    )

@router.get("/{watchlist_id}", response_model=WatchlistResponse)
def get_watchlist(
    watchlist_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get single watchlist by ID with live stock quotes."""
    wl = db.query(Watchlist).filter(Watchlist.id == watchlist_id, Watchlist.userId == current_user.id).first()
    if not wl:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    provider = get_market_data_provider()
    items_detail: List[WatchlistItemDetail] = []
    for item in wl.items:
        try:
            quote = provider.get_quote(item.symbol)
            price = quote.price
            change = quote.change
            pct = quote.percentageChange
            currency = quote.currency
            freshness = quote.freshness
        except Exception:
            price = None
            change = None
            pct = None
            currency = "₹"
            freshness = "UNAVAILABLE"

        th = item.thesis
        status_val = th.status if th else "NO_CHANGE"
        th_text = th.text if th else None
        th_cat = th.category if th else None
        th_evaluated = th.lastEvaluatedAt if th else None
        sig_count = len(th.signals) if (th and th.signals) else 0

        sup_count = len([e for e in th.evidence if e.classification == "SUPPORTING"]) if (th and th.evidence) else 0
        con_count = len([e for e in th.evidence if e.classification == "CONTRADICTING"]) if (th and th.evidence) else 0

        items_detail.append(WatchlistItemDetail(
            id=item.id,
            symbol=item.symbol,
            companyName=item.companyName,
            exchange=item.exchange,
            price=price,
            change=change,
            percentageChange=pct,
            currency=currency,
            thesisStatus=status_val,
            thesisText=th_text,
            thesisCategory=th_cat,
            signalCount=sig_count,
            supportingCount=sup_count,
            contradictingCount=con_count,
            freshness=freshness,
            lastEvaluatedAt=th_evaluated
        ))

    return WatchlistResponse(
        id=wl.id,
        userId=wl.userId,
        name=wl.name,
        createdAt=wl.createdAt,
        updatedAt=wl.updatedAt,
        items=items_detail
    )

@router.post("/{watchlist_id}/items", response_model=WatchlistItemDetail)
def add_stock_with_thesis(
    watchlist_id: str,
    item_in: WatchlistItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a real stock and structured thesis to watchlist."""
    wl = db.query(Watchlist).filter(Watchlist.id == watchlist_id, Watchlist.userId == current_user.id).first()
    if not wl:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    # Check for duplicate symbol in watchlist
    existing = db.query(WatchlistItem).filter(
        WatchlistItem.watchlistId == watchlist_id,
        WatchlistItem.symbol == item_in.symbol
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Stock {item_in.symbol} is already in your watchlist.")

    # 1. Create WatchlistItem
    item = WatchlistItem(
        watchlistId=watchlist_id,
        symbol=item_in.symbol,
        companyName=item_in.companyName,
        exchange=item_in.exchange
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    # 2. Interpret Thesis text & derive structured profile
    profile = thesis_interpreter.interpret(item_in.thesisText, item_in.category, item_in.companyName)

    # 3. Create Thesis record
    thesis = Thesis(
        userId=current_user.id,
        watchlistItemId=item.id,
        text=item_in.thesisText,
        category=item_in.category,
        status="NO_CHANGE"
    )
    db.add(thesis)
    db.commit()
    db.refresh(thesis)

    # 4. Create ThesisSignal records
    for sig in profile.signals:
        db_sig = ThesisSignal(
            thesisId=thesis.id,
            topic=sig.topic,
            signalName=sig.signalName,
            description=sig.targetMetric or sig.description,
            direction=sig.direction,
            importance=sig.importance,
            currentValue=None,
            previousValue=None
        )
        db.add(db_sig)
    db.commit()

    # 5. Run initial real market data fetch & evaluation
    provider = get_market_data_provider()
    try:
        quote = provider.get_quote(item.symbol)
        fund = provider.get_fundamentals(item.symbol)
        tech = provider.get_technicals(item.symbol)
        news_resp = news_service.get_ranked_news_for_thesis(
            item.symbol,
            item.companyName,
            thesis.text,
            [{"signalName": s.signalName, "topic": s.topic, "description": s.description} for s in thesis.signals]
        )
        # Evaluate thesis
        eval_resp = thesis_evaluator.evaluate_thesis(db, thesis, quote, fund, tech, news_resp)
        price = quote.price
        change = quote.change
        pct = quote.percentageChange
        curr = quote.currency
        status_val = eval_resp.status
        sup_cnt = eval_resp.supportingCount
        con_cnt = eval_resp.contradictingCount
        freshness = quote.freshness
    except Exception as e:
        logger.error(f"Initial evaluation error for {item.symbol}: {e}")
        price = 0.0
        change = 0.0
        pct = 0.0
        curr = "₹"
        status_val = "NO_CHANGE"
        sup_cnt = 0
        con_cnt = 0
        freshness = "LIVE"

    return WatchlistItemDetail(
        id=item.id,
        symbol=item.symbol,
        companyName=item.companyName,
        exchange=item.exchange,
        price=price,
        change=change,
        percentageChange=pct,
        currency=curr,
        thesisStatus=status_val,
        thesisText=thesis.text,
        thesisCategory=thesis.category,
        signalCount=len(profile.signals),
        supportingCount=sup_cnt,
        contradictingCount=con_cnt,
        freshness=freshness,
        lastEvaluatedAt=thesis.lastEvaluatedAt
    )

@router.delete("/{watchlist_id}/items/{symbol}")
def delete_stock(
    watchlist_id: str,
    symbol: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a stock and its thesis from watchlist."""
    item = db.query(WatchlistItem).join(Watchlist).filter(
        Watchlist.id == watchlist_id,
        Watchlist.userId == current_user.id,
        WatchlistItem.symbol == symbol
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Stock not found in watchlist")

    db.delete(item)
    db.commit()
    return {"message": f"Successfully removed {symbol} from watchlist."}
