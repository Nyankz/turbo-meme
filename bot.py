# renzo_bot.py (Сіздің Telegram бот — толық конфигурациямен)

import json
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher.filters import Command
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import logging
from aiogram.types import InputFile


# ========== CONFIG ==========
TOKEN = "7838676161:AAHt0qJoMwcezd_b1IHKUSAWjBsI2t9qpdw"
ADMIN_ID = 8100416617
KASPI_NUMBER = "+7 708 602 4478"
OWNER_NAME = "Раушангул.Б"
PRODUCT_FILE = "products.json"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# ========== STATES ==========
class PurchaseState(StatesGroup):
    waiting_for_payment = State()
    waiting_for_review = State()
    waiting_for_code = State()

# ========== UTILS ==========
def load_products():
    if os.path.exists(PRODUCT_FILE):
        with open(PRODUCT_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_products(data):
    with open(PRODUCT_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# ========== START ==========
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("📦 Категории"))

    photo = InputFile("IMG_20250614_232103_449.jpg")  # локал сурет

    await message.answer_photo(
        photo=photo,
        caption=f"Привет, {message.from_user.first_name}!\nВы попали на продажа бот РЕНЗО!\nЧто вы хотите? Выберите ниже 👇",
        reply_markup=kb
    )
# ========== КАТЕГОРИИ ==========
@dp.message_handler(text="📦 Категории")
async def show_categories(message: types.Message):
    data = load_products()
    if not data:
        return await message.answer("Категорий пока нет.")
    kb = InlineKeyboardMarkup()
    for cat in data:
        count = len(data[cat])
        kb.add(InlineKeyboardButton(f"{cat} ({count})", callback_data=f"cat_{cat}"))
    await message.answer("Выберите категорию:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("cat_"))
async def show_items(call: types.CallbackQuery):
    cat = call.data.split("_", 1)[1]
    data = load_products()
    items = data.get(cat, [])
    if not items:
        return await call.message.answer("Товаров нет в этой категории.")
    kb = InlineKeyboardMarkup()
    for idx, item in enumerate(items):
        kb.add(InlineKeyboardButton(f"{item}", callback_data=f"buy_{cat}_{idx}"))
    await call.message.answer(f"Товары в {cat}:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("buy_"))
async def handle_buy(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(item=call.data)
    await bot.send_message(call.from_user.id, f"💰 Оплатите 700 тг\n📱 Kaspi: {KASPI_NUMBER}\n\nОтправьте чек сюда (фото или PDF)")
    await state.set_state(PurchaseState.waiting_for_payment.state)

@dp.message_handler(content_types=types.ContentType.ANY, state=PurchaseState.waiting_for_payment)
async def handle_payment(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    await bot.send_message(ADMIN_ID, f"🧾 Новый чек от @{message.from_user.username or message.from_user.full_name}!")
    if message.photo:
        await bot.send_photo(ADMIN_ID, message.photo[-1].file_id)
    elif message.document:
        await bot.send_document(ADMIN_ID, message.document.file_id)
    await bot.send_message(ADMIN_ID, f"Отправьте номер: /send_number {message.from_user.id} <номер>")
    await state.finish()

# ========== SEND NUMBER ==========
@dp.message_handler(Command("send_number"), user_id=ADMIN_ID)
async def send_number(message: types.Message):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        return await message.reply("Формат: /send_number <user_id> <номер>")
    user_id = int(parts[1])
    number = parts[2]
    msg = (f"✅ Сделка успешно прошла!\n\n"
           f"📱 Номер: {number}\n👤 Имя владельца: {OWNER_NAME}\n\n"
           "❗ Важно:\nПосле входа в аккаунт обязательно:\n"
           "🔹 Смените почту\n🔹 Установите облачный пароль\n🔹 Включите двухфакторную аутентификацию\n\n"
           "🙏 Спасибо за внимание!\n\n✍️ Оставьте, пожалуйста, отзыв о боте 👇")
    await bot.send_message(user_id, msg)
    await bot.send_message(user_id, "✍️ Чтобы оставить отзыв, просто напишите сюда.")

# ========== ОТЗЫВ ==========
@dp.message_handler(lambda m: m.chat.id != ADMIN_ID)
async def receive_review(message: types.Message):
    await bot.send_message(ADMIN_ID, f"💬 Отзыв от @{message.from_user.username or message.from_user.full_name}:\n{message.text}")

# ========== АДМИН ПАНЕЛЬ ==========
@dp.message_handler(commands=['admin'], user_id=ADMIN_ID)
async def admin_panel(message: types.Message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("➕ Категория"), KeyboardButton("➕ Товар"))
    kb.add(KeyboardButton("📦 Категории"))
    await message.answer("Панель админа:", reply_markup=kb)

@dp.message_handler(text="➕ Категория", user_id=ADMIN_ID)
async def add_category(message: types.Message):
    await message.answer("Жаңа категория атын жазыңыз:")
    await PurchaseState.waiting_for_review.set()

@dp.message_handler(state=PurchaseState.waiting_for_review, user_id=ADMIN_ID)
async def save_category(message: types.Message, state: FSMContext):
    data = load_products()
    cat = message.text.strip()
    if cat not in data:
        data[cat] = []
        save_products(data)
        await message.answer(f"✅ Категория '{cat}' қосылды")
    else:
        await message.answer("❗ Бұл категория бұрыннан бар")
    await state.finish()

@dp.message_handler(text="➕ Товар", user_id=ADMIN_ID)
async def ask_category_for_item(message: types.Message):
    data = load_products()
    if not data:
        return await message.answer("Алдымен категория қосыңыз")
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for cat in data:
        kb.add(KeyboardButton(cat))
    await message.answer("Қай категорияға товар қосаңыз?", reply_markup=kb)
    await PurchaseState.waiting_for_review.set()

@dp.message_handler(state=PurchaseState.waiting_for_review, user_id=ADMIN_ID)
async def receive_item_category(message: types.Message, state: FSMContext):
    await state.update_data(category=message.text.strip())
    await message.answer("Товар атын жазыңыз:")
    await PurchaseState.waiting_for_code.set()

@dp.message_handler(state=PurchaseState.waiting_for_code, user_id=ADMIN_ID)
async def save_item(message: types.Message, state: FSMContext):
    data = await state.get_data()
    category = data.get("category")
    item = message.text.strip()
    products = load_products()
    if category in products:
        products[category].append(item)
        save_products(products)
        await message.answer(f"✅ Товар '{item}' добавлен в категорию '{category}'")
    else:
        await message.answer("❗ Категория не найдена")
    await state.finish()

# ========== START POLLING ==========
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
