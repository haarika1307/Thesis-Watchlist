import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from backend.app.db.base import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class ThesisSignal(Base):
    __tablename__ = "thesis_signals"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    thesisId = Column(String(36), ForeignKey("theses.id", ondelete="CASCADE"), nullable=False, index=True)
    topic = Column(String(100), nullable=False)
    signalName = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    direction = Column(String(20), nullable=False, default="POSITIVE")  # POSITIVE, NEGATIVE, NEUTRAL
    importance = Column(String(20), nullable=False, default="HIGH")  # HIGH, MEDIUM, LOW
    currentValue = Column(String(255), nullable=True)
    previousValue = Column(String(255), nullable=True)
    createdAt = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updatedAt = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    thesis = relationship("Thesis", back_populates="signals")
