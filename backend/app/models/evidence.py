import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.db.base import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    thesisId = Column(String(36), ForeignKey("theses.id", ondelete="CASCADE"), nullable=False, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    signalName = Column(String(150), nullable=False)
    sourceType = Column(String(50), nullable=False)  # FUNDAMENTAL, MARKET, NEWS, EVENT, MANAGEMENT
    sourceId = Column(String(100), nullable=True)
    previousValue = Column(String(255), nullable=True)
    currentValue = Column(String(255), nullable=True)
    changeValue = Column(String(255), nullable=True)
    changePercentage = Column(Float, nullable=True)
    classification = Column(String(20), nullable=False, default="NEUTRAL")  # SUPPORTING, CONTRADICTING, NEUTRAL, UNCERTAIN
    confidence = Column(Float, nullable=False, default=0.8)
    explanation = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Relationships
    thesis = relationship("Thesis", back_populates="evidence")
