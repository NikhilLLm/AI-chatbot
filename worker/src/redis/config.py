# import os
# from dotenv import load_dotenv
# from redis import asyncio as aioredis
# from rejson import Client

# load_dotenv(dotenv_path="C:/Users/nshej/chatbot/worker/two.env") #exolicity passing the path of env file

# class Redis():

#     def __init__(self):
#         """initialize the redis connection"""
#         self.REDIS_URL=os.environ.get("REDIS_URL")
#         self.REDIS_PASSWORD=os.environ.get("REDIS_PASSWORD")
#         self.REDIS_USER=os.environ.get("REDIS_USER")
#         self.connection_url = f"redis://{self.REDIS_USER}:{self.REDIS_PASSWORD}@{self.REDIS_URL}"
    
#     async def create_connection(self):
#         self.connection=aioredis.from_url(self.connection_url,db=0,decode_responses=True)

#         return self.connection
#     def create_rejson_connection(self):
#         self.redisJson=Client(host=self.REDIS_HOST,port=self.REDIS_PORT,decode_responses=True,username=self.REDIS_USER,password=self.REDIS_PASSWORD)

#         return self.redisJson
import os
from dotenv import load_dotenv
from redis import asyncio as aioredis
from redis.commands.json.path import Path
from redis import Redis as SyncRedis

# Load the .env file explicitly
load_dotenv(dotenv_path="C:/Users/nshej/chatbot/worker/two.env")

class Redis:
    def __init__(self):
        """Initialize the Redis connection settings"""
        self.REDIS_URL = os.environ.get("REDIS_URL")
        self.REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD")
        self.REDIS_USER = os.environ.get("REDIS_USER")

        # Keep same format for connection URL
        self.connection_url = f"redis://{self.REDIS_USER}:{self.REDIS_PASSWORD}@{self.REDIS_URL}"
        self.REDIS_HOST=os.environ.get("REDIS_HOST")
        self.REDIS_PORT = os.environ['REDIS_PORT']
        self.connection = None


    async def create_connection(self):
        """Creates async Redis connection (no change in usage)"""
        self.connection = aioredis.from_url(
            self.connection_url,
            db=0,
            decode_responses=True
        )
        return self.connection

    def create_rejson_connection(self):
        """
        Mimics old rejson.Client() behavior but uses built-in JSON support.
        This keeps same function name so other code continues to work.
        """
        if self.connection is None:
            # For sync-like access, create a simple Redis connection
            self.connection = SyncRedis.from_url(
                self.connection_url,
                db=0,
                decode_responses=True,
                host=self.REDIS_HOST,port=self.REDIS_PORT,username=self.REDIS_USER, password=self.REDIS_PASSWORD
            )
        # Return the same Redis connection (it already supports .json())
        return self.connection
