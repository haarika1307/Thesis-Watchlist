import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.orm import relationship
from backend.app.db.base import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class NewsArticle(Base):
    __tablename__ = "news_articles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    symbol = Column(String(50), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    source = Column(String(150), nullable=False)
    url = Column(String(1000), nullable=False)
    summary = Column(Text, nullable=True)
    publishedAt = Column(DateTime, nullable=True)
    fetchedAt = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    relevances = relationship("NewsRelevance", back_populates="article", cascade="all, delete-orphan")
