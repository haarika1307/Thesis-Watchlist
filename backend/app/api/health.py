from fastapi import APIRouter
from datetime import datetime, timezone
from backend.app.core.config import settings

router = APIRouter(tags=["Health"])

@router.get("/health")
def get_health():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "market_provider": settings.MARKET_DATA_PROVIDER,
        "news_provider": settings.NEWS_PROVIDER,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
