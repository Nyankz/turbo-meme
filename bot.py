import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import BOT_TOKEN, CHANNEL_ID
from database import *
from scheduler import schedule_battle_end, scheduler
from uuid import uuid4

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(F.text == "/start")
async def start(message: types.Message):
    await message.answer("📸 Фото немесе видео жіберіңіз (батл үшін)")

@dp.message(F.content_type.in_({"photo", "video"}))
async def get_media(message: types.Message):
    media_id = message.photo[-1].file_id if message.photo else message.video.file_id
    await message.answer("👤 Атыңыз кім?")
    dp.message.register(handle_name, media_id=media_id)

async def handle_name(message: types.Message, media_id):
    name = message.text
    add_user(message.from_user.id, message.from_user.username, media_id, name)

    opponent = get_waiting_user()
    if opponent and opponent[0] != message.from_user.id:
        battle_id = str(uuid4())[:8]
        start_time, end_time = start_battle(battle_id, message.from_user.id, opponent[0])

        # Дауысты батырмалар
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"✅ {name}", url=f"https://t.me/{bot.username}?start={battle_id}_{name}")],
            [InlineKeyboardButton(text=f"✅ {opponent[3]}", url=f"https://t.me/{bot.username}?start={battle_id}_{opponent[3]}")]
        ])

        await bot.send_message(CHANNEL_ID, f"🔥 Батл басталды!\n{name} vs {opponent[3]}", reply_markup=kb)

        schedule_battle_end(bot, battle_id, end_time)
    else:
        await message.answer("🕓 Жұп табылғанша күтіңіз...")

@dp.message(F.text.regexp(r"^/start (.+)$"))
async def vote(message: types.Message):
    args = message.get_args()
    battle_id, voted_for = args.split("_")
    battle = get_battle(battle_id)

    if not battle:
        await message.answer("❌ Батл табылмады")
        return

    from datetime import datetime
    if datetime.now().isoformat() > battle[4]:
        await message.answer("⏰ Батл уақыты аяқталған")
        return

    if has_voted(message.from_user.id, battle_id):
        await message.answer("✅ Сен дауыс беріп қойғансың!")
        return

    add_vote(message.from_user.id, battle_id, voted_for)
    await message.answer(f"✅ Дауыс берілді: {voted_for}")

async def main():
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())