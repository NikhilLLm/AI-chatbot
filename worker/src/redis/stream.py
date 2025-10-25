
from .config import Redis
class StreamConsumer:
    def __init__(self, redis_client):
        self.redis_client = redis_client
        self.last_ids = {}  # Track last read ID for each channel

    async def consume_stream(self, count: int, block: int, stream_channel):
        # Read only new messages (avoid replay) using '$'
        response = await self.redis_client.xread(
            streams={stream_channel: '$'}, count=count, block=block)
        
        return response

    async def delete_message(self, stream_channel, message_id):
        await self.redis_client.xdel(stream_channel, message_id)