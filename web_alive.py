from fastapi import FastAPI, Request
from aiogram import types
from bot import dp  # импорт диспетчера из bot.py

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
