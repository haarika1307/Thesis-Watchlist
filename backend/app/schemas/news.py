from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class NewsArticleResponse(BaseModel):
    id: Optional[str] = None
    symbol: str
    title: str
    source: str
    url: str
    summary: Optional[str] = None
    publishedAt: Optional[datetime] = None
    relevanceScore: Optional[float] = None
    classification: Optional[str] = None  # SUPPORTING, CONTRADICTING, NEUTRAL, UNCERTAIN
    reason: Optional[str] = None

    class Config:
        from_attributes = True

class NewsListResponse(BaseModel):
    symbol: str
    relevantNews: List[NewsArticleResponse] = []
    allNews: List[NewsArticleResponse] = []
