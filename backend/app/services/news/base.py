from abc import ABC, abstractmethod
from typing import List
from backend.app.schemas.news import NewsArticleResponse

class NewsProvider(ABC):
    """Abstract Base Class for News Providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    def get_company_news(self, symbol: str, company_name: str = "") -> List[NewsArticleResponse]:
        """Fetch real company news articles."""
        pass
