import asyncio
import uvicorn
from multiprocessing import Process
from bot import run_bot
from web_alive import app
from dotenv import load_dotenv
import os

load_dotenv()

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
DATABASE_URL = os.getenv("DATABASE_URL")

def run_api():
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    p = Process(target=run_api)
    p.start()
    asyncio.run(run_bot())
