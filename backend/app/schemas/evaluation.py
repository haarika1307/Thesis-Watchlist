from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class EvaluationResponse(BaseModel):
    id: str
    thesisId: str
    status: str  # STRENGTHENING, NEEDS_ATTENTION, NO_CHANGE
    supportingCount: int
    contradictingCount: int
    neutralCount: int
    confidence: float
    summary: str
    evaluatedAt: datetime

    class Config:
        from_attributes = True

class WatchlistSummaryResponse(BaseModel):
    watchlistId: Optional[str] = None
    lastCheckedAt: Optional[datetime] = None
    thesisChangedCount: int = 0
    needsAttentionCount: int = 0
    noChangeCount: int = 0
    totalStocks: int = 0

class EvaluationRunResponse(BaseModel):
    message: str
    evaluationsRun: int
    summary: WatchlistSummaryResponse
