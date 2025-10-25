from fastapi import WebSocket,status,Query,WebSocketException
from typing import Optional
from worker.src.redis.config import Redis
redis=Redis()



async def get_token(websocket: WebSocket, token: Optional[str] = Query(None)):
    if not token:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Missing token")
    try:
        # Fail fast if Redis is slow/unavailable
        import asyncio
        redis_client = await asyncio.wait_for(redis.create_connection(), timeout=2.0)
        exists = await asyncio.wait_for(redis_client.exists(f"token:{token}"), timeout=2.0)
        if exists:
            print("✅ Token is valid")
            return token
        else:
            print("❌ Token not found or expired")
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid or expired token")
    except Exception as e:
        # Soft-allow on infra hiccups so UI doesn't hang forever
        print(f"⚠️ Redis check failed ({e}). Allowing token to avoid handshake hang.")
        return token