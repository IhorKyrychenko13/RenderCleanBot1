
import asyncio
import uvicorn
from multiprocessing import Process
from bot import run_bot
from web_alive import app

def run_api():
    uvicorn.run(app, host="0.0.0.0", port=10000)

if __name__ == "__main__":
    p = Process(target=run_api)
    p.start()
    asyncio.run(run_bot())
