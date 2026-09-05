import logging
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.app.workers.market_updates import market_stream_manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])

@router.websocket("/ws/market")
async def websocket_market_stream(websocket: WebSocket):
    """WebSocket endpoint for subscribing to live market quotes without full-page reloads."""
    await market_stream_manager.connect(websocket)
    try:
        while True:
            data_text = await websocket.receive_text()
            try:
                msg = json.loads(data_text)
                action = msg.get("action")
                if action == "subscribe":
                    symbols = msg.get("symbols", [])
                    if isinstance(symbols, list):
                        market_stream_manager.subscribe(websocket, symbols)
                        await websocket.send_json({
                            "type": "SUBSCRIBED",
                            "symbols": symbols
                        })
                elif action == "ping":
                    await websocket.send_json({"type": "pong"})
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        market_stream_manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket error: {e}")
        market_stream_manager.disconnect(websocket)
