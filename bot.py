from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram.filters import CommandStart
import asyncio
from config import TOKEN
from handlers import router  # <--- МІНДЕТТІ!

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
dp.include_router(router)  # <--- Хандлерді қосу

@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer("Сәлем! Батл үшін фото/видео жібер.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

