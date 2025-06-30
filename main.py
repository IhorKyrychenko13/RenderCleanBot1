from aiogram import Bot, Dispatcher, types
import os
from fastapi import FastAPI, Request
from dotenv import load_dotenv
import uvicorn
from bot import router  # твой роутер с хендлерами

load_dotenv()

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise RuntimeError("TOKEN is not set in environment variables")

bot = Bot(token=TOKEN)
dp = Dispatcher()  # БЕЗ параметров

dp.include_router(router)

app = FastAPI()

@app.post("/webhook_path")
async def webhook(request: Request):
    data = await request.json()
    update = types.Update(**data)
    await dp.feed_update(update)
    return {"ok": True}

@app.get("/")
async def root():
    return {"status": "ok"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
