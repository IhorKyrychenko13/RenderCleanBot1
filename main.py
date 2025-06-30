import asyncio
import uvicorn
from multiprocessing import Process
from bot import run_bot
from web_alive import app
import os
from dotenv import load_dotenv

load_dotenv()

def run_api():
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    p = Process(target=run_api)
    p.start()
    asyncio.run(run_bot())
