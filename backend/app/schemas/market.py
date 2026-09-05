from pydantic import BaseModel
from typing import Optional, List, Any, Dict
from datetime import datetime

class StockSearchResult(BaseModel):
    symbol: str
    name: str
    exchange: str = "NSE"
    currency: str = "INR"
    type: str = "EQUITY"
    price: Optional[float] = None
    change: Optional[float] = None
    percentageChange: Optional[float] = None

class QuoteResponse(BaseModel):
    symbol: str
    companyName: str
    price: float
    change: float
    percentageChange: float
    currency: str = "INR"
    exchange: str = "NSE"
    dayHigh: Optional[float] = None
    dayLow: Optional[float] = None
    fiftyTwoWeekHigh: Optional[float] = None
    fiftyTwoWeekLow: Optional[float] = None
    marketCap: Optional[float] = None
    volume: Optional[int] = None
    pe: Optional[float] = None
    marketStatus: str = "OPEN"  # OPEN, CLOSED, PRE, POST
    freshness: str = "LIVE"  # LIVE, DELAYED, AS OF ...
    provider: str = "yahoo"
    timestamp: datetime

class HistoryCandle(BaseModel):
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: int

class HistoryResponse(BaseModel):
    symbol: str
    range: str
    candles: List[HistoryCandle]

class FinancialPeriod(BaseModel):
    period: str
    revenue: Optional[float] = None
    netIncome: Optional[float] = None
    operatingMargin: Optional[float] = None
    eps: Optional[float] = None

class FundamentalsResponse(BaseModel):
    symbol: str
    companyName: Optional[str] = None
    marketCap: Optional[float] = None
    pe: Optional[float] = None
    pb: Optional[float] = None
    roe: Optional[float] = None
    roce: Optional[float] = None
    eps: Optional[float] = None
    dividendYield: Optional[float] = None
    revenue: Optional[float] = None
    profit: Optional[float] = None
    ebitda: Optional[float] = None
    margin: Optional[float] = None
    debt: Optional[float] = None
    freeCashFlow: Optional[float] = None
    financialHistory: List[FinancialPeriod] = []
    freshness: str = "AS OF LATEST FILING"
    provider: str = "yahoo"
    timestamp: datetime

class TechnicalsResponse(BaseModel):
    symbol: str
    price: float
    volume: int
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macdSignal: Optional[float] = None
    macdHist: Optional[float] = None
    sma20: Optional[float] = None
    sma50: Optional[float] = None
    sma200: Optional[float] = None
    volatility: Optional[float] = None
    trend: Optional[str] = None
    timestamp: datetime
