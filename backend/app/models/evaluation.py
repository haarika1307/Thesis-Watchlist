import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.db.base import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    thesisId = Column(String(36), ForeignKey("theses.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), nullable=False)  # STRENGTHENING, NEEDS_ATTENTION, NO_CHANGE
    supportingCount = Column(Integer, nullable=False, default=0)
    contradictingCount = Column(Integer, nullable=False, default=0)
    neutralCount = Column(Integer, nullable=False, default=0)
    confidence = Column(Float, nullable=False, default=0.85)
    summary = Column(Text, nullable=False)
    evaluatedAt = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Relationships
    thesis = relationship("Thesis", back_populates="evaluations")

class WatchlistEvaluation(Base):
    __tablename__ = "watchlist_evaluations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    watchlistId = Column(String(36), ForeignKey("watchlists.id", ondelete="CASCADE"), nullable=False, index=True)
    lastCheckedAt = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    thesisChangedCount = Column(Integer, nullable=False, default=0)
    needsAttentionCount = Column(Integer, nullable=False, default=0)
    noChangeCount = Column(Integer, nullable=False, default=0)

    # Relationships
    watchlist = relationship("Watchlist", back_populates="evaluations")
