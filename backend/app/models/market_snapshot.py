import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, BigInteger, DateTime
from backend.app.db.base import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class MarketSnapshot(Base):
    __tablename__ = "market_snapshots"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    symbol = Column(String(50), nullable=False, index=True)
    price = Column(Float, nullable=False)
    percentageChange = Column(Float, nullable=True)
    volume = Column(BigInteger, nullable=True)
    volatility = Column(Float, nullable=True)
    marketCap = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
