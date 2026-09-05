from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ThesisSignalBase(BaseModel):
    topic: str
    signalName: str
    description: Optional[str] = None
    direction: str = "POSITIVE"  # POSITIVE, NEGATIVE, NEUTRAL
    importance: str = "HIGH"  # HIGH, MEDIUM, LOW
    currentValue: Optional[str] = None
    previousValue: Optional[str] = None

class ThesisSignalCreate(ThesisSignalBase):
    pass

class ThesisSignalResponse(ThesisSignalBase):
    id: str
    thesisId: str
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True

class SignalDefinition(BaseModel):
    signalName: str
    topic: str
    description: str
    direction: str = "POSITIVE"
    importance: str = "HIGH"
    targetMetric: Optional[str] = None  # e.g., "revenueGrowth", "operatingMargin", "pe", "priceChange"
    newsKeywords: List[str] = []

class StructuredThesisProfile(BaseModel):
    business: Optional[str] = None
    theme: str  # Growth, Valuation, Turnaround, Margin Expansion, Demand Recovery, Risk, Event
    rationale: str
    signals: List[SignalDefinition]

class ThesisCreate(BaseModel):
    category: str = "Growth"
    text: str = Field(..., min_length=3, max_length=2000)

class ThesisUpdate(BaseModel):
    category: Optional[str] = None
    text: Optional[str] = None

class ThesisResponse(BaseModel):
    id: str
    userId: str
    watchlistItemId: str
    text: str
    category: str
    status: str  # STRENGTHENING, NEEDS_ATTENTION, NO_CHANGE
    createdAt: datetime
    updatedAt: datetime
    lastEvaluatedAt: Optional[datetime] = None
    signals: List[ThesisSignalResponse] = []

    class Config:
        from_attributes = True
