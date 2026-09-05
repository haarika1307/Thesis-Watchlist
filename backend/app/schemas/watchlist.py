from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from backend.app.schemas.thesis import ThesisResponse

class WatchlistItemCreate(BaseModel):
    symbol: str
    companyName: str
    exchange: str = "NSE"
    category: str = "Growth"
    thesisText: str = Field(..., min_length=3)

class WatchlistItemResponse(BaseModel):
    id: str
    watchlistId: str
    symbol: str
    companyName: str
    exchange: str
    createdAt: datetime
    updatedAt: datetime
    thesis: Optional[ThesisResponse] = None

    class Config:
        from_attributes = True

class WatchlistItemDetail(BaseModel):
    id: str
    symbol: str
    companyName: str
    exchange: str
    price: Optional[float] = None
    change: Optional[float] = None
    percentageChange: Optional[float] = None
    currency: str = "INR"
    thesisStatus: str = "NO_CHANGE"  # STRENGTHENING, NEEDS_ATTENTION, NO_CHANGE
    thesisText: Optional[str] = None
    thesisCategory: Optional[str] = None
    signalCount: int = 0
    supportingCount: int = 0
    contradictingCount: int = 0
    freshness: str = "LIVE"
    lastEvaluatedAt: Optional[datetime] = None

class WatchlistCreate(BaseModel):
    name: str = "My Watchlist"

class WatchlistResponse(BaseModel):
    id: str
    userId: str
    name: str
    createdAt: datetime
    updatedAt: datetime
    items: List[WatchlistItemDetail] = []

    class Config:
        from_attributes = True
