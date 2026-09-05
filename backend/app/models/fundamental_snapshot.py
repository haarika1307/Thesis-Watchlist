import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime
from backend.app.db.base import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class FundamentalSnapshot(Base):
    __tablename__ = "fundamental_snapshots"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    symbol = Column(String(50), nullable=False, index=True)
    pe = Column(Float, nullable=True)
    pb = Column(Float, nullable=True)
    eps = Column(Float, nullable=True)
    roe = Column(Float, nullable=True)
    roce = Column(Float, nullable=True)
    revenue = Column(Float, nullable=True)
    profit = Column(Float, nullable=True)
    ebitda = Column(Float, nullable=True)
    margin = Column(Float, nullable=True)
    debt = Column(Float, nullable=True)
    freeCashFlow = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
