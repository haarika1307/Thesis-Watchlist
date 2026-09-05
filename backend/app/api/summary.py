import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.models.user import User
from backend.app.models.watchlist import Watchlist
from backend.app.models.watchlist_item import WatchlistItem
from backend.app.models.evaluation import WatchlistEvaluation
from backend.app.schemas.evaluation import WatchlistSummaryResponse, EvaluationRunResponse
from backend.app.services.market_data.provider_factory import get_market_data_provider
from backend.app.services.news.news_service import news_service
from backend.app.services.evaluation.evaluator import thesis_evaluator
from backend.app.api.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Watchlist Summary & Batch Evaluation"])

@router.get("/watchlist/summary", response_model=WatchlistSummaryResponse)
def get_watchlist_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve summary metrics for the initial Smart Watchlist screen."""
    watchlist = db.query(Watchlist).filter(Watchlist.userId == current_user.id).first()
    if not watchlist:
        return WatchlistSummaryResponse(
            lastCheckedAt=datetime.now(timezone.utc),
            thesisChangedCount=0,
            needsAttentionCount=0,
            noChangeCount=0,
            totalStocks=0
        )

    # Calculate actual counts across watchlist items
    items = watchlist.items
    total_stocks = len(items)
    
    thesis_changed = 0
    needs_attention = 0
    no_change = 0
    latest_evaluated_at = None

    for item in items:
        if item.thesis:
            st = item.thesis.status
            if item.thesis.lastEvaluatedAt:
                if latest_evaluated_at is None or item.thesis.lastEvaluatedAt > latest_evaluated_at:
                    latest_evaluated_at = item.thesis.lastEvaluatedAt

            if st == "STRENGTHENING":
                thesis_changed += 1
            elif st == "NEEDS_ATTENTION":
                needs_attention += 1
            else:
                no_change += 1
        else:
            no_change += 1

    # Check for recent WatchlistEvaluation record
    last_eval = db.query(WatchlistEvaluation)\
        .filter(WatchlistEvaluation.watchlistId == watchlist.id)\
        .order_by(WatchlistEvaluation.lastCheckedAt.desc())\
        .first()

    checked_at = latest_evaluated_at or (last_eval.lastCheckedAt if last_eval else datetime.now(timezone.utc))

    return WatchlistSummaryResponse(
        watchlistId=watchlist.id,
        lastCheckedAt=checked_at,
        thesisChangedCount=thesis_changed,
        needsAttentionCount=needs_attention,
        noChangeCount=no_change,
        totalStocks=total_stocks
    )

@router.post("/evaluations/run", response_model=EvaluationRunResponse)
def run_all_evaluations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Run batch evaluations across all watchlist items and update overall summary."""
    watchlist = db.query(Watchlist).filter(Watchlist.userId == current_user.id).first()
    if not watchlist or not watchlist.items:
        return EvaluationRunResponse(
            message="No stocks in watchlist to evaluate.",
            evaluationsRun=0,
            summary=WatchlistSummaryResponse(
                lastCheckedAt=datetime.now(timezone.utc),
                thesisChangedCount=0,
                needsAttentionCount=0,
                noChangeCount=0,
                totalStocks=0
            )
        )

    provider = get_market_data_provider()
    eval_count = 0

    for item in watchlist.items:
        if item.thesis:
            try:
                quote = provider.get_quote(item.symbol)
                fund = provider.get_fundamentals(item.symbol)
                tech = provider.get_technicals(item.symbol)
                news = news_service.get_ranked_news_for_thesis(
                    item.symbol,
                    item.companyName,
                    item.thesis.text,
                    [{"signalName": s.signalName, "topic": s.topic, "description": s.description} for s in item.thesis.signals]
                )
                thesis_evaluator.evaluate_thesis(db, item.thesis, quote, fund, tech, news)
                eval_count += 1
            except Exception as e:
                logger.error(f"Error evaluating {item.symbol}: {e}")

    # Aggregate evaluation
    w_eval = thesis_evaluator.evaluate_watchlist(db, watchlist.id)

    return EvaluationRunResponse(
        message=f"Evaluations successfully completed for {eval_count} stocks.",
        evaluationsRun=eval_count,
        summary=WatchlistSummaryResponse(
            watchlistId=watchlist.id,
            lastCheckedAt=w_eval.lastCheckedAt,
            thesisChangedCount=w_eval.thesisChangedCount,
            needsAttentionCount=w_eval.needsAttentionCount,
            noChangeCount=w_eval.noChangeCount,
            totalStocks=len(watchlist.items)
        )
    )
