from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ObjectiveChangeResponse(BaseModel):
    id: str
    signalName: str
    category: str      # MARKET, FUNDAMENTALS, COMPANY, NEWS
    sourceType: str    # MARKET, FUNDAMENTAL, NEWS, MANAGEMENT, EVENT
    previousValue: Optional[str] = None
    currentValue: str
    changeValue: Optional[str] = None
    changePercentage: Optional[float] = None
    magnitude: Optional[str] = None
    isMeaningful: bool = True
    significanceReason: str = ""
    thesisImpact: str = "NEUTRAL"  # SUPPORTING, CONTRADICTING, NEUTRAL

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
    status: str  # NO_MEANINGFUL_CHANGE, MEANINGFUL_CHANGE, THESIS_STRENGTHENING, THESIS_NEEDS_ATTENTION
    hasMeaningfulChange: bool = False
    meaningfulChangeCount: int = 0
    supportingCount: int
    contradictingCount: int
    neutralCount: int
    summary: str
    lastCheckedAt: Optional[datetime] = None
    lastEvaluatedAt: Optional[datetime] = None
    objectiveChanges: List[ObjectiveChangeResponse] = []
    supportingEvidence: List[EvidenceResponse] = []
    contradictingEvidence: List[EvidenceResponse] = []
    neutralEvidence: List[EvidenceResponse] = []

