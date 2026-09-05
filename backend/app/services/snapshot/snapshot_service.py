import logging
from datetime import datetime, timezone
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.models.market_snapshot import MarketSnapshot
from backend.app.models.fundamental_snapshot import FundamentalSnapshot
from backend.app.schemas.market import QuoteResponse, FundamentalsResponse

logger = logging.getLogger(__name__)

class SnapshotService:
    """Service to capture and retrieve historical market and fundamental snapshots for change detection."""

    def capture_market_snapshot(
        self,
        db: Session,
        symbol: str,
        quote: QuoteResponse,
        volatility: Optional[float] = None
    ) -> MarketSnapshot:
        """Store a new MarketSnapshot row."""
        snapshot = MarketSnapshot(
            symbol=symbol,
            price=quote.price,
            percentageChange=quote.percentageChange,
            volume=quote.volume,
            volatility=volatility,
            marketCap=quote.marketCap,
            timestamp=datetime.now(timezone.utc)
        )
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)
        return snapshot

    def capture_fundamental_snapshot(
        self,
        db: Session,
        symbol: str,
        fundamentals: FundamentalsResponse
    ) -> FundamentalSnapshot:
        """Store a new FundamentalSnapshot row."""
        snapshot = FundamentalSnapshot(
            symbol=symbol,
            pe=fundamentals.pe,
            pb=fundamentals.pb,
            eps=fundamentals.eps,
            roe=fundamentals.roe,
            roce=fundamentals.roce,
            revenue=fundamentals.revenue,
            profit=fundamentals.profit,
            ebitda=fundamentals.ebitda,
            margin=fundamentals.margin,
            debt=fundamentals.debt,
            freeCashFlow=fundamentals.freeCashFlow,
            timestamp=datetime.now(timezone.utc)
        )
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)
        return snapshot

    def get_latest_snapshots(
        self,
        db: Session,
        symbol: str
    ) -> Tuple[Optional[MarketSnapshot], Optional[MarketSnapshot]]:
        """Get the current latest and previous market snapshots for change comparison."""
        snapshots = db.query(MarketSnapshot)\
            .filter(MarketSnapshot.symbol == symbol)\
            .order_by(desc(MarketSnapshot.timestamp))\
            .limit(2)\
            .all()

        current = snapshots[0] if len(snapshots) > 0 else None
        previous = snapshots[1] if len(snapshots) > 1 else None
        return current, previous

    def get_fundamental_snapshots(
        self,
        db: Session,
        symbol: str
    ) -> Tuple[Optional[FundamentalSnapshot], Optional[FundamentalSnapshot]]:
        """Get the current latest and previous fundamental snapshots."""
        snapshots = db.query(FundamentalSnapshot)\
            .filter(FundamentalSnapshot.symbol == symbol)\
            .order_by(desc(FundamentalSnapshot.timestamp))\
            .limit(2)\
            .all()

        current = snapshots[0] if len(snapshots) > 0 else None
        previous = snapshots[1] if len(snapshots) > 1 else None
        return current, previous

snapshot_service = SnapshotService()
