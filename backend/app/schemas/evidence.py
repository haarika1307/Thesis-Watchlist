from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class EvidenceResponse(BaseModel):
    id: str
    thesisId: str
    symbol: str
    signalName: str
    sourceType: str  # FUNDAMENTAL, MARKET, NEWS, EVENT, MANAGEMENT
    sourceId: Optional[str] = None
    previousValue: Optional[str] = None
    currentValue: Optional[str] = None
    changeValue: Optional[str] = None
    changePercentage: Optional[float] = None
    classification: str  # SUPPORTING, CONTRADICTING, NEUTRAL, UNCERTAIN
    confidence: float
    explanation: str
    timestamp: datetime

    class Config:
        from_attributes = True

class WhatChangedResponse(BaseModel):
    symbol: str
    companyName: str
    thesisId: str
    thesisText: str
    thesisCategory: str
    status: str  # STRENGTHENING, NEEDS_ATTENTION, NO_CHANGE
    supportingCount: int
    contradictingCount: int
    neutralCount: int
    summary: str
    lastEvaluatedAt: Optional[datetime] = None
    supportingEvidence: List[EvidenceResponse] = []
    contradictingEvidence: List[EvidenceResponse] = []
    neutralEvidence: List[EvidenceResponse] = []
