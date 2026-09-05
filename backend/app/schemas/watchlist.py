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
    thesisStatus: str = "NO_CHANGE"  # NO_MEANINGFUL_CHANGE, MEANINGFUL_CHANGE, THESIS_STRENGTHENING, THESIS_NEEDS_ATTENTION
    hasMeaningfulChange: bool = False
    meaningfulChangeCount: int = 0
    thesisText: Optional[str] = None
    thesisCategory: Optional[str] = None
    signalCount: int = 0
    supportingCount: int = 0
    contradictingCount: int = 0
    freshness: str = "LIVE"
    lastCheckedAt: Optional[datetime] = None
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
