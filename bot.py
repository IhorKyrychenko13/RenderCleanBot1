import asyncio
import os
import psycopg2
from psycopg2 import OperationalError
from aiogram import Bot, Dispatcher, Router, types
from aiogram.types import Message
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
DATABASE_URL = os.getenv("DATABASE_URL")

bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()

keywords = ["запрещённое слово1", "запрещённое слово2", "запрещённое слово3"]

def get_db_connection():
    try:
        return psycopg2.connect(DATABASE_URL)
    except OperationalError as e:
        print(f"Ошибка подключения к базе данных: {e}")
        return None

def initialize_database():
    conn = get_db_connection()
    if conn is None:
        print("Не удалось подключиться к базе данных для инициализации")
        return
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                text TEXT,
                date TIMESTAMP,
                thread_id INTEGER,
                UNIQUE(text, thread_id)
            )
        """)
        conn.commit()
        print("Таблица messages успешно инициализирована")
    except Exception as e:
        print(f"Ошибка при инициализации базы данных: {e}")
    finally:
        conn.close()

initialize_database()

def normalize_text(text):
    return ' '.join(text.split()).lower().strip() if text else ""

async def delete_bot_message(message):
    await asyncio.sleep(60)
    try:
        await message.delete()
        print(f"✅ Сообщение от бота удалено через минуту: {message.message_id}")
    except Exception as e:
        print(f"Ошибка при удалении сообщения от бота: {e}")

@router.message()
async def check_and_delete(message: Message):
    if message.chat.id != CHANNEL_ID:
        print(f"Сообщение из другой группы: {message.chat.id}, игнорируем")
        return

    if message.from_user.username == "GroupHelp":
        raw_text = message.text or message.caption or ""
        print(f"Сообщение от GroupHelp: {raw_text}")
        if any(keyword.lower() in raw_text.lower() for keyword in keywords):
            print("Обнаружено запрещённое сообщение от GroupHelp. Удаляем.")
            await message.delete()
        else:
            print("Запрещённые слова в сообщении от GroupHelp не обнаружены.")
        return

    raw_text = message.text or message.caption or ""
    text = normalize_text(raw_text)
    thread_id = message.message_thread_id if message.is_topic_message else 0
    username = message.from_user.username or message.from_user.full_name
    photo_count = len(message.photo or [])

    print(f"Получено сообщение от @{username}: {text if text else '[Без текста]'}. Изображения: {photo_count}")

    conn = get_db_connection()
    if conn is None:
        print("Не удалось подключиться к базе данных для проверки сообщений")
        return

    try:
        cursor = conn.cursor()
        if text:
            cursor.execute(
                """
                SELECT date FROM messages
                WHERE text = %s AND thread_id = %s AND date > CURRENT_TIMESTAMP - INTERVAL '7 days'
                """, (text, thread_id)
            )
            result = cursor.fetchone()
            if result:
                print(f"❌ Сообщение от @{username} дублирует предыдущее. Удаляем.")
                await message.delete()
                bot_message = await bot.send_message(
                    message.chat.id,
                    f"❌ @{username}, вы уже публиковали такое объявление за последние 7 дней.",
                    message_thread_id=thread_id
                )
                asyncio.create_task(delete_bot_message(bot_message))
                return

        cursor.execute(
            "INSERT INTO messages (text, date, thread_id) VALUES (%s, CURRENT_TIMESTAMP, %s)",
            (text if text else "[Без текста]", thread_id)
        )
        conn.commit()
        print(f"✅ Сообщение от @{username} сохранено.")
    except Exception as e:
        print(f"Ошибка при работе с базой данных: {e}")
    finally:
        conn.close()

async def run_bot():
    dp.include_router(router)
    print("Бот запущен и ждет обновлений по вебхуку")
    # Не используем polling, т.к. webhook — бот запускается с внешним сервером
    await asyncio.Event().wait()
