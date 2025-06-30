
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

@router.message()
async def handler(message: Message):
    await message.answer("Работает")

async def start_bot():
    dp.include_router(router)
    await dp.start_polling(bot)
