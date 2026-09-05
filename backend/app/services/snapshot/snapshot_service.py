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

    def get_last_check_session(
        self,
        db: Session,
        watchlistItemId: str,
        symbol: str
    ):
        """Retrieve the latest persisted check session for a stock."""
        from backend.app.models.check_session import CheckSession
        return db.query(CheckSession)\
            .filter(CheckSession.watchlistItemId == watchlistItemId, CheckSession.symbol == symbol)\
            .order_by(desc(CheckSession.checkedAt))\
            .first()

    def record_check_session(
        self,
        db: Session,
        watchlistItemId: str,
        symbol: str,
        price: Optional[float] = None,
        change: Optional[float] = None,
        percentageChange: Optional[float] = None,
        volume: Optional[int] = None,
        volatility: Optional[float] = None,
        pe: Optional[float] = None,
        pb: Optional[float] = None,
        eps: Optional[float] = None,
        roe: Optional[float] = None,
        margin: Optional[float] = None,
        revenue: Optional[float] = None,
        profit: Optional[float] = None,
        debt: Optional[float] = None,
        latestHeadline: Optional[str] = None,
        newsCount: int = 0,
        overallStatus: str = "NO_MEANINGFUL_CHANGE",
        hasMeaningfulChange: bool = False,
        meaningfulChangeCount: int = 0,
        supportingCount: int = 0,
        contradictingCount: int = 0,
        neutralCount: int = 0
    ):
        """Record or update a check session for a watchlist item."""
        from backend.app.models.check_session import CheckSession
        now = datetime.now(timezone.utc)
        
        session = CheckSession(
            watchlistItemId=watchlistItemId,
            symbol=symbol,
            checkedAt=now,
            price=price,
            change=change,
            percentageChange=percentageChange,
            volume=volume,
            volatility=volatility,
            pe=pe,
            pb=pb,
            eps=eps,
            roe=roe,
            margin=margin,
            revenue=revenue,
            profit=profit,
            debt=debt,
            latestHeadline=latestHeadline,
            newsCount=newsCount,
            overallStatus=overallStatus,
            hasMeaningfulChange=1 if hasMeaningfulChange else 0,
            meaningfulChangeCount=meaningfulChangeCount,
            supportingCount=supportingCount,
            contradictingCount=contradictingCount,
            neutralCount=neutralCount
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

snapshot_service = SnapshotService()
