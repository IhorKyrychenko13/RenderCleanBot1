from fastapi import FastAPI, Request
from aiogram import types, Dispatcher

app = FastAPI()
dp = Dispatcher()  # твой диспетчер с хендлерами

@app.post("/webhook_path")
async def webhook(request: Request):
    data = await request.json()
    update = types.Update(**data)
    await dp.feed_update(update)  # feed_update, а не process_update
    return {"ok": True}

@app.get("/")
async def root():
    return {"status": "ok"}
