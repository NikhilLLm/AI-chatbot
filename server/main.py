from fastapi import FastAPI,Request
import uvicorn
import os
from dotenv import load_dotenv
from server.src.routes.chat import chat



load_dotenv(dotenv_path="C:/Users/nshej/chatbot/server/touch.env") #exolicity passing the path of env file
print("Environment:",os.environ.get('APP_ENV'))
api=FastAPI()
api.include_router(chat)



@api.get("/test")

async def root():
    return {"msg":"API is working fine"}


if __name__=="__main__":
    if os.environ.get('APP_ENV')=="development":
        uvicorn.run("server.main:api",host="0.0.0.0",port=3500,workers=4,reload=True)
    else:
        pass



