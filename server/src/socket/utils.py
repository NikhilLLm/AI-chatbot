from fastapi import WebSocket,status,Query,WebSocketException
from typing import Optional
from worker.src.redis.config import Redis
redis=Redis()



async def get_token(websocket: WebSocket, token: Optional[str] = Query(None)):
    if not token:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Missing token")

    redis_client = await redis.create_connection()
    
    # Check if token key exists
    exists = await redis_client.exists(f"token:{token}")
    
    if exists:
        print("✅ Token is valid")
        return token
    else:
        print("❌ Token not found or expired")
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid or expired token")