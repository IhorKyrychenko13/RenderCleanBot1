import os
import asyncio
import psycopg2
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message
from dotenv import load_dotenv
from psycopg2 import OperationalError

load_dotenv()

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
DATABASE_URL = os.getenv("DATABASE_URL")

bot = Bot(token=TOKEN, parse_mode="HTML")
dp = Dispatcher()

keywords = ["запрещённое слово1", "запрещённое слово2", "запрещённое слово3"]

def get_db_connection():
    try:
        return psycopg2.connect(DATABASE_URL)
    except OperationalError as e:
        print(f"❌ Ошибка подключения к базе данных: {e}")
        return None

def initialize_database():
    conn = get_db_connection()
    if conn is None:
        return
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    text TEXT,
                    date TIMESTAMP,
                    thread_id INTEGER,
                    UNIQUE(text, thread_id)
                )
            """)
            conn.commit()
            print("✅ Таблица messages инициализирована")
    except Exception as e:
        print(f"Ошибка при создании таблицы: {e}")
    finally:
        conn.close()

def normalize_text(text):
    return ' '.join(text.split()).lower().strip() if text else ""

async def delete_bot_message(message: types.Message):
    await asyncio.sleep(60)
    try:
        await message.delete()
        print(f"✅ Удалено: {message.message_id}")
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")

@dp.message(F.chat.id == CHANNEL_ID)
async def check_and_delete(message: Message):
    raw_text = message.text or message.caption or ""
    thread_id = message.message_thread_id if message.is_topic_message else 0
    username = message.from_user.username or message.from_user.full_name

    # Проверка на бота GroupHelp
    if message.from_user.username == "GroupHelp":
        if any(k.lower() in raw_text.lower() for k in keywords):
            await message.delete()
        return

    text = normalize_text(raw_text)
    conn = get_db_connection()
    if not conn:
        return

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 1 FROM messages
                WHERE text = %s AND thread_id = %s AND date > CURRENT_TIMESTAMP - INTERVAL '7 days'
            """, (text, thread_id))
            if cursor.fetchone():
                await message.delete()
                reply = await message.answer(
                    f"❌ @{username}, вы уже публиковали такое объявление за последние 7 дней.",
                    reply_to_message_id=message.message_id
                )
                asyncio.create_task(delete_bot_message(reply))
                return

            cursor.execute(
                "INSERT INTO messages (text, date, thread_id) VALUES (%s, CURRENT_TIMESTAMP, %s)",
                (text or "[Без текста]", thread_id)
            )
            conn.commit()
    except Exception as e:
        print(f"Ошибка при записи в БД: {e}")
    finally:
        conn.close()
