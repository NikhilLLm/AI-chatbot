from worker.src.redis.config import Redis
from .src.model.gptj import GPT
from .src.schema.chat import Message
from .src.redis.cache import Cache
from .src.redis.stream import StreamConsumer
from .src.redis.producer import Producer
import os
import asyncio
redis=Redis()

async def main():
    try:
        json_client = redis.create_rejson_connection()
        redis_client = await redis.create_connection()
        consumer = StreamConsumer(redis_client)
        producer = Producer(redis_client)
        cache = Cache(json_client)
        print("🚀 Stream consumer started")
        print("👂 Waiting for messages...")
        
        while True:
            try:
                print("🔄 Checking message channel...")
                response = await consumer.consume_stream(count=1, block=2000, stream_channel="message_channel")
                print("📩 Stream response:", response)
                
                if response:
                    for stream, messages in response:
                        for message in messages:
                            try:
                                message_id = message[0]
                                token = [k for k,v in message[1].items()][0]
                                raw_msg = [v for k,v in message[1].items()][0]
                                print("📥 Received message:", token, raw_msg)

                                msg = Message(msg=raw_msg)
                                await cache.add_message_to_cache(token=token, source="human", message_data=msg.model_dump())

                                data = await cache.get_chat_history(token=token)
                                message_data = data['messages'][-1:]
                                input = ["" + i['msg'] for i in message_data]
                                input = " ".join(input)
                            
                                res = GPT().query(input=input)
                                print("🤖 GPT Response:", res)
                                if res is None:
                                    print("❌ GPT response failed. Skipping message creation.")
                                    continue
                            
                                msg = Message(msg=res)
                                
                                # Add bot message to cache
                                await cache.add_message_to_cache(token=token, source="bot", message_data=msg.model_dump())
                                
                                # Structure and send response
                                stream_data = {
                                    "token": token,
                                    "msg": msg.msg
                                }
                                
                                # Send to response channel and log
                                await producer.add_to_stream(stream_data, "response_channel")
                                print("✈️ Sent response to stream:", stream_data)
                            
                            except Exception as e:
                                print(f"❌ Error processing message: {str(e)}")
                            finally:
                                # Always try to clean up the consumed message
                                await consumer.delete_message(stream_channel="message_channel", message_id=message_id)
            except Exception as e:
                print(f"❌ Stream processing error: {str(e)}")
                await asyncio.sleep(1)  # Wait before retrying
    except Exception as e:
        print(f"❌ Critical error: {str(e)}")
        raise  # Re-raise to exit the program
          
          
   
if __name__=="__main__":
    asyncio.run(main())