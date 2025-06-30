import os
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types
from dotenv import load_dotenv
import uvicorn
from your_router_module import router  # импортируй этот модуль с твоим router

load_dotenv()

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise RuntimeError("TOKEN не установлен")

bot = Bot(token=TOKEN)
dp = Dispatcher()

dp.include_router(router)  # подключаем роутер один раз здесь

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
