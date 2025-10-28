import os
from dotenv import load_dotenv
import aiohttp
import json
import asyncio

# Load .env file (update with your path)
load_dotenv(dotenv_path="C:/Users/nshej/chatbot/worker/two.env")


class GPT:
    def __init__(self):
        # Load API endpoint and key from environment variables
        self.url = os.environ.get("MODEL_URL")
        self.api_key = os.environ.get("HUGGINFACE_INFERENCE_TOKEN")  # reused variable name
        self.site_url = os.environ.get("YOUR_SITE_URL", "")
        self.site_name = os.environ.get("YOUR_SITE_NAME", "")

        # Base headers for OpenRouter API
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Optional metadata headers for OpenRouter ranking
        if self.site_url:
            self.headers["HTTP-Referer"] = self.site_url
        if self.site_name:
            self.headers["X-Title"] = self.site_name

        # Base payload structure (model + messages)
        self.payload = {
            "model": "qwen/qwen2.5-vl-72b-instruct",
            "messages": [{"role": "user", "content": ""}],
            "parameters":{
                "return_full_text": False,
                "use_cache":False,
                "max_new_tokens":25,
            }
        }

    async def query(self, input: str):
        # Update payload with user message
        self.payload["messages"] = [{"role": "user", "content": input}]

        # Show waiting message before the request
        print("⏳ Waiting for model to respond...")
 
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.url,
                    headers=self.headers,
                    json=self.payload,
                    timeout=60
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        text = data["choices"][0]["message"]["content"]
                        res = str(text.split("Human:")[0]).strip("\n").strip()
                        print("✅ Model responded successfully!\n")
                        return res
                    elif response.status == 503:
                        print("⏳ Model is loading, try again in ~20 seconds")
                    else:
                        text = await response.text()
                        print(f"❌ Error {response.status}: {text}")
                    return None
 
        except Exception as e:
            print(f"❌ Error: {e}")
            return None


if __name__ == "__main__":
    gpt = GPT()
    
