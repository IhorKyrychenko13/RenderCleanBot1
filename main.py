from fastapi import FastAPI, Request
from aiogram import types
from bot import bot, dp

app = FastAPI()

@app.post("/webhook_path")
async def webhook(request: Request):
    data = await request.json()
    update = types.Update(**data)
    await dp.feed_update(update, bot=bot)
    return {"ok": True}

@app.get("/")
async def root():
    return {"status": "ok"}
