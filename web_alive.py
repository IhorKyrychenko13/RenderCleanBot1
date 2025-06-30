from fastapi import FastAPI, Request
from aiogram import types
from bot import dp  # импорт твоего Dispatcher

app = FastAPI()

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = types.Update(**data)
    await dp.process_update(update)  # <-- правильно вызываем процессинг обновления
    return {"ok": True}

@app.get("/")
async def root():
    return {"status": "ok"}
