import os
import asyncio
import asyncpg
from aiogram import Bot, Dispatcher, types
from aiogram.types import Update
from fastapi import FastAPI, Request
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
DATABASE_URL = os.getenv("DATABASE_URL")

bot = Bot(token=TOKEN)
dp = Dispatcher()

app = FastAPI()

# При старте создаём пул и сохраняем в app.state
@app.on_event("startup")
async def startup():
    app.state.db_pool = await asyncpg.create_pool(DATABASE_URL)
    async with app.state.db_pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                text TEXT,
                date TIMESTAMP DEFAULT now(),
                thread_id INTEGER,
                UNIQUE(text, thread_id)
            );
        """)

# При остановке закрываем пул
@app.on_event("shutdown")
async def shutdown():
    await app.state.db_pool.close()

# Нормализация текста (приведение к нижнему регистру, убираем лишние пробелы)
def normalize_text(text: str) -> str:
    if not text:
        return ""
    return ' '.join(text.lower().strip().split())

# Задача для удаления сообщения бота через 60 секунд
async def delete_bot_message(message: types.Message):
    await asyncio.sleep(60)
    try:
        await message.delete()
    except Exception:
        pass

# Хэндлер для проверки и удаления дубликатов
@dp.message()
async def check_and_delete(message: types.Message):
    # Берём пул из глобального app
    db_pool = app.state.db_pool

    if message.chat.id != CHANNEL_ID:
        return

    raw_text = message.text or message.caption or ""
    text = normalize_text(raw_text)
    thread_id = message.message_thread_id if hasattr(message, "message_thread_id") else 0
    username = message.from_user.username or message.from_user.full_name

    if not text:
        return

    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT date FROM messages
            WHERE text = $1 AND thread_id = $2 AND date > NOW() - INTERVAL '7 days'
            """,
            text, thread_id
        )

        if row:
            try:
                await message.delete()
            except Exception:
                pass

            bot_message = await message.answer(
                f"❌ @{username}, такое сообщение уже было за последние 7 дней.",
                reply_to_message_id=message.message_id
            )
            asyncio.create_task(delete_bot_message(bot_message))
            return

        try:
            await conn.execute(
                "INSERT INTO messages (text, thread_id) VALUES ($1, $2) ON CONFLICT DO NOTHING",
                text, thread_id
            )
        except Exception:
            pass

# Webhook для FastAPI, чтобы получать обновления из Telegram
@app.post("/webhook_path")
async def webhook(request: Request):
    data = await request.json()
    update = Update(**data)
    await dp.feed_update(bot, update)
    return {"ok": True}

@app.get("/")
async def root():
    return {"status": "ok"}
