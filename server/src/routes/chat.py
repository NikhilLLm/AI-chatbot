import os
from fastapi import APIRouter,Request,WebSocket,FastAPI,HTTPException, WebSocketDisconnect
import uuid
from fastapi.params import Depends
from pydantic import BaseModel
from ..socket.connection import ConnectionManager
from ..socket.utils import get_token
from worker.src.redis.config import Redis
from worker.src.redis.producer import Producer
from server.src.schema.chat import Chat,Message
from redis.commands.json.path import Path
from worker.src.redis.stream import StreamConsumer
from worker.src.redis.cache import Cache
chat=APIRouter()

manager=ConnectionManager()
redis=Redis()


@chat.post("/token")
async def token_generator(name: str, request: Request):

    if name == "":
        raise HTTPException(status_code=400, detail={
            "loc": "name",  "msg": "Enter a valid name"})

    token = str(uuid.uuid4())

    #create new chat session

    json_client=redis.create_rejson_connection()

    chat_session=Chat(token=token,messages=[],name=name)
    print(chat_session.dict())

    json_client.json().set(str(token), Path.root_path(), chat_session.dict())

    redis_client=await redis.create_connection()

    await redis_client.set(f"token:{token}", "valid", ex=3600)  #setting expiry of 24 hours

    return chat_session.dict()

@chat.post("/refresh_token")

async def refresh_token(request:Request,token:str):
    json_client=redis.create_rejson_connection()
    cache=Cache(json_client)
    data=await cache.get_chat_history(token)
    if data==None:
        raise HTTPException(
            status_code=400, detail="Session expired or does not exist")
    else:
        return data

@chat.websocket("/chat")
async def websocket_endpoint(websocket: WebSocket,token:str=Depends(get_token)):
 
    await manager.connect(websocket)
    redis_client=await redis.create_connection()
    consumer=StreamConsumer(redis_client)
    # Ensure we don't miss fast responses: start reading response_channel from beginning
    consumer.last_ids["response_channel"] = "0-0"
    producer=Producer(redis_client)
    json_client = redis.create_rejson_connection()
    try:
        while True:
            data=await websocket.receive_text()
            print(f"📨 Received from WebSocket: {data}")
            # Ignore heartbeats and empty payloads
            # if not data:
            #     print("⏭️ Skipping empty message")
            #     continue
            # try:
            #     if data.startswith('{'):
            #         maybe = __import__('json').loads(data)
            #         if isinstance(maybe, dict) and maybe.get('type') == 'ping':
            #             print("⏭️ Skipping heartbeat ping")
            #             continue
            # except Exception:
            #     pass
            # # Skip only zero-width heartbeat (do not skip normal whitespace)
            # if data == '\u200b':
            #     print("⏭️ Skipping whitespace/zero-width message")
            #     continue

            print(f"📤 Forwarding to Redis stream: token={token}, data={data}")
            stream_data={}
            stream_data[token]=data
            await producer.add_to_stream(stream_data,"message_channel")
            print(f"✅ Message added to message_channel")

            # Wait up to ~15s for a response from the worker (15 x 1s)
            found = False
            for _ in range(15):
                response = await consumer.consume_stream(count=10, block=1000, stream_channel="response_channel")
                if not response:
                    continue
                print(response)
                for stream, messages in response:
                    for message in messages:
                        response_token = message[1].get(b"token") or message[1].get("token")
                        response_msg = message[1].get(b"msg") or message[1].get("msg")

                        if response_token and response_msg:
                            response_token = response_token.decode() if isinstance(response_token, bytes) else response_token
                            response_msg = response_msg.decode() if isinstance(response_msg, bytes) else response_msg

                            if token == response_token:
                                print("✅ Token matched. Sending response...")
                                await manager.send_personal_message(response_msg, websocket)
                                found = True
                                # Delete only the message we processed for this token
                                await consumer.delete_message(stream_channel="response_channel", message_id=message[0])
                            else:
                                # Do NOT delete messages meant for other tokens
                                pass
                if found:
                    break
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# Simple echo WebSocket to validate connectivity without token/Redis
@chat.websocket("/ws_test")
async def websocket_test(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            data = await ws.receive_text()
            await ws.send_text(f"echo: {data}")
    except WebSocketDisconnect:
        pass


