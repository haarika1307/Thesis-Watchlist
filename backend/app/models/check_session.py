import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, BigInteger, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.app.db.base import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class CheckSession(Base):
    """Stores a user's observation checkpoint for a watchlist item to compare future checks against."""
    __tablename__ = "check_sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    watchlistItemId = Column(String(36), ForeignKey("watchlist_items.id", ondelete="CASCADE"), nullable=False, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    checkedAt = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Market state at check
    price = Column(Float, nullable=True)
    change = Column(Float, nullable=True)
    percentageChange = Column(Float, nullable=True)
    volume = Column(BigInteger, nullable=True)
    volatility = Column(Float, nullable=True)

    # Fundamental state at check
    pe = Column(Float, nullable=True)
    pb = Column(Float, nullable=True)
    eps = Column(Float, nullable=True)
    roe = Column(Float, nullable=True)
    margin = Column(Float, nullable=True)
    revenue = Column(Float, nullable=True)
    profit = Column(Float, nullable=True)
    debt = Column(Float, nullable=True)

    # News & Company developments state
    latestHeadline = Column(Text, nullable=True)
    newsCount = Column(Integer, default=0)

    # Change classification results
    overallStatus = Column(String(50), default="NO_MEANINGFUL_CHANGE") # NO_MEANINGFUL_CHANGE, MEANINGFUL_CHANGE, THESIS_STRENGTHENING, THESIS_NEEDS_ATTENTION
    hasMeaningfulChange = Column(Boolean, default=False)
    meaningfulChangeCount = Column(Integer, default=0)
    supportingCount = Column(Integer, default=0)
    contradictingCount = Column(Integer, default=0)
    neutralCount = Column(Integer, default=0)

    # Relationship
    watchlistItem = relationship("WatchlistItem", backref="check_sessions")
