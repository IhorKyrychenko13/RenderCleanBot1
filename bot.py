import os
import asyncio
import asyncpg
from aiogram import Bot, Dispatcher, types
from fastapi import FastAPI, Request
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
DATABASE_URL = os.getenv("DATABASE_URL")

bot = Bot(token=TOKEN)
dp = Dispatcher()

app = FastAPI()

db_pool: asyncpg.Pool | None = None  # Глобальная переменная пула БД

async def create_db_pool():
    return await asyncpg.create_pool(DATABASE_URL)

@app.on_event("startup")
async def startup():
    global db_pool
    db_pool = await create_db_pool()
    async with db_pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                text TEXT,
                date TIMESTAMP DEFAULT now(),
                thread_id INTEGER,
                UNIQUE(text, thread_id)
            );
        """)

@app.post("/webhook_path")
async def webhook(request: Request):
    data = await request.json()
    update = types.Update(**data)
    await dp.feed_update(update)
    return {"ok": True}

@app.get("/")
async def root():
    return {"status": "ok"}

async def delete_bot_message(message: types.Message):
    await asyncio.sleep(60)
    try:
        await message.delete()
    except Exception:
        pass

def normalize_text(text: str) -> str:
    if not text:
        return ""
    return ' '.join(text.lower().strip().split())

@dp.message()
async def check_and_delete(message: types.Message):
    if message.chat.id != CHANNEL_ID:
        return

    raw_text = message.text or message.caption or ""
    text = normalize_text(raw_text)
    thread_id = message.message_thread_id if hasattr(message, "message_thread_id") else 0
    username = message.from_user.username or message.from_user.full_name

    if not text:
        return

    global db_pool
    if db_pool is None:
        print("DB pool not initialized!")
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
