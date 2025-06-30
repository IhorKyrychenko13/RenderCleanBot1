from fastapi import FastAPI, Request
from aiogram import types
from bot import dp

app = FastAPI()

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = types.Update(**data)
    await dp.feed_update(update)
    return {"ok": True}
