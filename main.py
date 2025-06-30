import os
import asyncio
import asyncpg
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Update, Message
from fastapi import FastAPI, Request
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
DATABASE_URL = os.getenv("DATABASE_URL")

bot = Bot(token=TOKEN)
dp = Dispatcher()
app = FastAPI()

# Запрещённые слова от GroupHelp
FORBIDDEN_WORDS = ["запрещённое слово1", "запрещённое слово2", "запрещённое слово3"]

# Создаём пул подключений к базе при старте
@app.on_event("startup")
async def on_startup():
    app.state.db = await asyncpg.create_pool(DATABASE_URL)
    async with app.state.db.acquire() as conn:
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            text TEXT,
            date TIMESTAMP DEFAULT now(),
            thread_id INTEGER,
            UNIQUE(text, thread_id)
        );
        """)

@app.on_event("shutdown")
async def on_shutdown():
    await app.state.db.close()

def normalize_text(text: str) -> str:
    return ' '.join(text.strip().lower().split()) if text else ""

# Удаление сообщения бота через 60 сек
async def delete_bot_message(message: Message):
    await asyncio.sleep(60)
    try:
        await message.delete()
    except:
        pass

@dp.message()
async def handle_message(message: Message):
    if message.chat.id != CHANNEL_ID:
        return

    db_pool = app.state.db
    text_raw = message.text or message.caption or ""
    text = normalize_text(text_raw)
    thread_id = message.message_thread_id if message.is_topic_message else 0
    username = message.from_user.username or message.from_user.full_name
    user_tag = f"@{username}"

    # 📛 Обработка GroupHelp
    if message.from_user.username == "GroupHelp":
        if any(word in text.lower() for word in FORBIDDEN_WORDS):
            try:
                await message.delete()
            except:
                pass
        return

    photo_count = len(message.photo or [])

    if not text and not photo_count:
        return  # Пустое сообщение, не обрабатываем

    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT date FROM messages
            WHERE text = $1 AND thread_id = $2 AND date > NOW() - INTERVAL '7 days'
        """, text if text else "[без текста]", thread_id)

        if row:
            try:
                await message.delete()
            except:
                pass
            bot_msg = await message.answer(
                f"❌ {user_tag}, вы уже публиковали такое сообщение за последние 7 дней.",
                reply_to_message_id=message.message_id
            )
            asyncio.create_task(delete_bot_message(bot_msg))
            return

        try:
            await conn.execute("""
                INSERT INTO messages (text, thread_id)
                VALUES ($1, $2) ON CONFLICT DO NOTHING
            """, text if text else "[без текста]", thread_id)
        except:
            pass

# Webhook
@app.post("/webhook")
async def webhook_handler(request: Request):
    data = await request.json()
    update = Update(**data)
    await dp.feed_update(bot, update)
    return {"ok": True}

@app.get("/")
async def root():
    return {"status": "ok"}