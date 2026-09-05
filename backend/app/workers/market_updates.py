import asyncio
import logging
from typing import Set, Dict, Any, List
from fastapi import WebSocket

from backend.app.services.market_data.provider_factory import get_market_data_provider

logger = logging.getLogger(__name__)

class MarketStreamManager:
    """Manages WebSocket connections and broadcasts real-time/delayed market state to connected clients."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.subscribed_symbols: Dict[str, Set[WebSocket]] = {}
        self._is_running = False

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket client connected. Active: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        for sym, subs in list(self.subscribed_symbols.items()):
            subs.discard(websocket)
            if not subs:
                del self.subscribed_symbols[sym]
        logger.info(f"WebSocket client disconnected. Active: {len(self.active_connections)}")

    def subscribe(self, websocket: WebSocket, symbols: List[str]):
        for sym in symbols:
            norm = sym.upper()
            if norm not in self.subscribed_symbols:
                self.subscribed_symbols[norm] = set()
            self.subscribed_symbols[norm].add(websocket)

    async def broadcast_symbol_update(self, symbol: str, quote_data: Dict[str, Any]):
        """Push updated price and volume to all subscribers of this symbol."""
        norm = symbol.upper()
        if norm in self.subscribed_symbols:
            subscribers = list(self.subscribed_symbols[norm])
            for ws in subscribers:
                try:
                    await ws.send_json({
                        "type": "QUOTE_UPDATE",
                        "symbol": symbol,
                        "data": quote_data
                    })
                except Exception:
                    self.disconnect(ws)

    async def start_background_stream(self):
        """Background loop updating quotes periodically for watched symbols."""
        if self._is_running:
            return
        self._is_running = True
        provider = get_market_data_provider()

        while self._is_running:
            try:
                if self.subscribed_symbols:
                    for sym in list(self.subscribed_symbols.keys()):
                        try:
                            quote = provider.get_quote(sym)
                            await self.broadcast_symbol_update(sym, {
                                "price": quote.price,
                                "change": quote.change,
                                "percentageChange": quote.percentageChange,
                                "volume": quote.volume,
                                "currency": quote.currency,
                                "freshness": quote.freshness,
                                "timestamp": quote.timestamp.isoformat()
                            })
                        except Exception as e:
                            logger.debug(f"Stream error for {sym}: {e}")
            except Exception as e:
                logger.error(f"Error in background stream loop: {e}")

            await asyncio.sleep(15)  # Polling interval for market provider

market_stream_manager = MarketStreamManager()
