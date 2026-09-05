from abc import ABC, abstractmethod
from typing import List, Optional
from backend.app.schemas.market import (
    StockSearchResult,
    QuoteResponse,
    HistoryResponse,
    FundamentalsResponse,
    TechnicalsResponse
)

class MarketDataProvider(ABC):
    """Abstract Base Class for Market Data Providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    def search(self, query: str) -> List[StockSearchResult]:
        """Search for real stocks/companies matching query."""
        pass

    @abstractmethod
    def get_quote(self, symbol: str) -> QuoteResponse:
        """Fetch current real-time or delayed quote."""
        pass

    @abstractmethod
    def get_history(self, symbol: str, range_str: str = "1M") -> HistoryResponse:
        """Fetch real historical OHLCV candles (1D, 1W, 1M, 6M, 1Y, 5Y, ALL)."""
        pass

    @abstractmethod
    def get_fundamentals(self, symbol: str) -> FundamentalsResponse:
        """Fetch real financial statements, ratios, and fundamentals."""
        pass

    @abstractmethod
    def get_technicals(self, symbol: str) -> TechnicalsResponse:
        """Compute real technical indicators (RSI, MACD, SMAs, Volatility) from price history."""
        pass
