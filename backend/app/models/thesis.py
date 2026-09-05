import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.db.base import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class Thesis(Base):
    __tablename__ = "theses"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    userId = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    watchlistItemId = Column(String(36), ForeignKey("watchlist_items.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    text = Column(Text, nullable=False)
    category = Column(String(50), nullable=False, default="Growth")
    status = Column(String(50), nullable=False, default="NO_CHANGE")  # STRENGTHENING, NEEDS_ATTENTION, NO_CHANGE
    createdAt = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updatedAt = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    lastEvaluatedAt = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="theses")
    watchlist_item = relationship("WatchlistItem", back_populates="thesis")
    signals = relationship("ThesisSignal", back_populates="thesis", cascade="all, delete-orphan")
    evidence = relationship("Evidence", back_populates="thesis", cascade="all, delete-orphan")
    news_relevance = relationship("NewsRelevance", back_populates="thesis", cascade="all, delete-orphan")
    evaluations = relationship("Evaluation", back_populates="thesis", cascade="all, delete-orphan")
