import asyncio
import uvicorn
from bot import start_bot
from web_alive import app

async def main():
    await asyncio.gather(
        start_bot(),
    )

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    uvicorn.run("web_alive:app", host="0.0.0.0", port=10000)
