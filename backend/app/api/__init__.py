from backend.app.api.health import router as health_router
from backend.app.api.auth import router as auth_router
from backend.app.api.stocks import router as stocks_router
from backend.app.api.watchlists import router as watchlists_router
from backend.app.api.theses import router as theses_router
from backend.app.api.summary import router as summary_router
from backend.app.api.ws import router as ws_router

__all__ = [
    "health_router",
    "auth_router",
    "stocks_router",
    "watchlists_router",
    "theses_router",
    "summary_router",
    "ws_router",
]
