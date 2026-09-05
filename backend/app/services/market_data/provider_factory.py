from backend.app.core.config import settings
from backend.app.services.market_data.base import MarketDataProvider
from backend.app.services.market_data.yahoo_provider import YahooMarketDataProvider

_provider_instance: MarketDataProvider = None

def get_market_data_provider() -> MarketDataProvider:
    """Return configured MarketDataProvider singleton."""
    global _provider_instance
    if _provider_instance is None:
        # Currently defaults to production Yahoo provider (can be extended to Upstox/Zerodha)
        _provider_instance = YahooMarketDataProvider()
    return _provider_instance
