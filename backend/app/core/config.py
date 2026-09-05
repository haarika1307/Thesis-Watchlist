import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # App
    APP_NAME: str = "Smart Watchlist"
    APP_VERSION: str = "1.0.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "sqlite:///./smart_watchlist.db"

    # Security
    JWT_SECRET: str = "c84910e53a2ef819bc8d5930129a28e83b4b576829a8f4c2810471b6d0812903"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Market Data
    MARKET_DATA_PROVIDER: str = "yahoo"  # "yahoo", "upstox", "zerodha"
    MARKET_DATA_API_KEY: Optional[str] = None
    MARKET_CACHE_TTL_SECONDS: int = 60  # Cache real quotes for 60 seconds
    HISTORY_CACHE_TTL_SECONDS: int = 300  # 5 minutes for price candles
    FUNDAMENTALS_CACHE_TTL_SECONDS: int = 3600  # 1 hour for fundamentals

    # News Provider
    NEWS_PROVIDER: str = "yahoo"  # "yahoo", "newsapi", "finnhub"
    NEWS_API_KEY: Optional[str] = None
    NEWS_CACHE_TTL_SECONDS: int = 900  # 15 minutes

    # Intelligence / LLM
    LLM_PROVIDER: str = "builtin"  # "builtin", "openai", "gemini"
    LLM_API_KEY: Optional[str] = None

    # CORS
    FRONTEND_ORIGIN: str = "*"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
