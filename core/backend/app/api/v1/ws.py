"""WebSocket endpoint for admin-panel real-time alerts (e.g. NEW_ORDER toasts).
Auth: `?token=<jwt>` query param. Subscribes the connection to Redis pub/sub
channel `ws:alerts:{merchant_id}` and forwards every message verbatim."""
import asyncio
import json
from uuid import UUID

import structlog
from fastapi import WebSocket, WebSocketDisconnect, status
from redis.asyncio import Redis

from app.core.redis import get_redis
from app.core.security import decode_token

logger = structlog.get_logger()


async def alerts_socket(websocket: WebSocket) -> None:
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        payload = decode_token(token)
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    if payload.get("type") == "refresh":
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    merchant_id_raw = payload.get("merchant_id")
    if not merchant_id_raw:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    try:
        merchant_id = UUID(merchant_id_raw)
    except ValueError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    channel = f"ws:alerts:{merchant_id}"
    redis: Redis = await get_redis()
    pubsub = redis.pubsub()
    await pubsub.subscribe(channel)
    logger.info("ws_alerts_subscribed", merchant_id=str(merchant_id), channel=channel)

    try:
        # Send a hello so the frontend knows we're live
        await websocket.send_json({"type": "HELLO", "payload": {"merchant_id": str(merchant_id)}})
        while True:
            msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=30.0)
            if msg and msg.get("type") == "message":
                data = msg.get("data")
                if isinstance(data, bytes):
                    data = data.decode()
                try:
                    parsed = json.loads(data) if isinstance(data, str) else data
                except json.JSONDecodeError:
                    parsed = {"type": "RAW", "payload": data}
                await websocket.send_json(parsed)
            # Periodic ping so idle clients don't get cut by proxies
            await asyncio.sleep(0)
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.warning("ws_alerts_error", error=str(exc))
    finally:
        try:
            await pubsub.unsubscribe(channel)
            await pubsub.aclose()
        except Exception:
            pass
        logger.info("ws_alerts_closed", merchant_id=str(merchant_id))
