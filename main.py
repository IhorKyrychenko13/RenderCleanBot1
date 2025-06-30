import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from dotenv import load_dotenv
from bot import dp, initialize_database  # импорт диспетчера и инициализация БД

load_dotenv()

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise RuntimeError("TOKEN не установлен")

bot = Bot(token=TOKEN)
dp.bot = bot  # обязательно для aiogram v2

initialize_database()

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
