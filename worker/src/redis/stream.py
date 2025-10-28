
from .config import Redis
class StreamConsumer:
    def __init__(self, redis_client):
        self.redis_client = redis_client
        self.last_ids = {}  # Track last read ID for each channel

    async def consume_stream(self, count: int, block: int, stream_channel):
        # Use the last known ID or '0' for first read to ensure we don't miss messages
        last_id = self.last_ids.get(stream_channel, '0')
        
        response = await self.redis_client.xread(
            streams={stream_channel: last_id}, 
            count=count, 
            block=block
        )
        
        # Update last_id if we got messages
        if response:
            for stream_name, messages in response:
                if messages:
                    self.last_ids[stream_channel] = messages[-1][0]
                    print(f"📝 Updated last_id for {stream_channel}: {self.last_ids[stream_channel]}")
        
        return response

    async def delete_message(self, stream_channel, message_id):
        await self.redis_client.xdel(stream_channel, message_id)