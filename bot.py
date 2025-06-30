from aiogram import Router, types
import asyncio

router = Router()

FORBIDDEN_WORDS = ["запрещённое слово1", "запрещённое слово2", "запрещённое слово3"]
CHANNEL_ID = None  # Пока None, будем задавать позже

def set_channel_id(channel_id: int):
    global CHANNEL_ID
    CHANNEL_ID = channel_id

def normalize_text(text: str) -> str:
    return ' '.join(text.strip().lower().split()) if text else ""

async def delete_bot_message(message: types.Message):
    await asyncio.sleep(60)
    try:
        await message.delete()
    except:
        pass

@router.message()
async def handle_message(message: types.Message):
    if message.chat.id != CHANNEL_ID:
        return

    text_raw = message.text or message.caption or ""
    text = normalize_text(text_raw)
    thread_id = message.message_thread_id if message.is_topic_message else 0
    username = message.from_user.username or message.from_user.full_name
    user_tag = f"@{username}"

    # Обработка GroupHelp
    if message.from_user.username == "GroupHelp":
        if any(word in text.lower() for word in FORBIDDEN_WORDS):
            try:
                await message.delete()
            except:
                pass
        return

    photo_count = len(message.photo or [])
    if not text and not photo_count:
        return

    # db_pool нужно получить снаружи, например, через message.bot["db_pool"]
    db_pool = message.bot['db_pool']
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
