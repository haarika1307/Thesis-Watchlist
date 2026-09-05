import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.db.base import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class NewsRelevance(Base):
    __tablename__ = "news_relevance"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    newsArticleId = Column(String(36), ForeignKey("news_articles.id", ondelete="CASCADE"), nullable=False, index=True)
    thesisId = Column(String(36), ForeignKey("theses.id", ondelete="CASCADE"), nullable=False, index=True)
    relevanceScore = Column(Float, nullable=False, default=0.0)
    classification = Column(String(20), nullable=False, default="NEUTRAL")  # SUPPORTING, CONTRADICTING, NEUTRAL, UNCERTAIN
    reason = Column(Text, nullable=True)
    createdAt = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    article = relationship("NewsArticle", back_populates="relevances")
    thesis = relationship("Thesis", back_populates="news_relevance")
