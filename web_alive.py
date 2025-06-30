from fastapi import FastAPI, Request
from aiogram import types
from bot import dp, bot  # импортируем из bot.py

app = FastAPI()

@app.post("/webhook_path")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = types.Update(**data)
    await dp.process_update(update)
    return {"ok": True}

@app.on_event("startup")
async def on_startup():
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(url="https://dekete.onrender.com/webhook_path")

@app.on_event("shutdown")
async def on_shutdown():
    await bot.session.close()
