import json
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Command
from aiogram.types import InputFile

TOKEN = "7838676161:AAHt0qJoMwcezd_b1IHKUSAWjBsI2t9qpdw"
ADMIN_ID = 8100416617
OWNER_NAME = "Раушангул.Б"
KASPI_NUMBER = "+7 708 602 4478"
PRODUCT_FILE = "products.json"

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

class PurchaseState(StatesGroup):
    waiting_for_payment = State()
    waiting_for_category = State()
    waiting_for_item = State()
    waiting_for_number = State()
    waiting_for_code_request = State()
    waiting_for_code_send = State()
    waiting_for_review = State()

def load_products():
    if os.path.exists(PRODUCT_FILE):
        with open(PRODUCT_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_products(data):
    with open(PRODUCT_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("📦 Категории"))
    photo = InputFile("IMG_20250614_232103_449.jpg")
    await message.answer_photo(
        photo=photo,
        caption=f"Привет, {message.from_user.first_name}!\nВы попали на продажа бот РЕНЗО!\nЧто вы хотите? Выберите ниже 👇",
        reply_markup=kb
    )

@dp.message_handler(text="📦 Категории")
async def show_categories(message: types.Message):
    data = load_products()
    if not data:
        return await message.answer("Категорий пока нет.")
    kb = InlineKeyboardMarkup()
    for cat in data:
        kb.add(InlineKeyboardButton(f"{cat}", callback_data=f"cat_{cat}"))
    await message.answer("Выберите категорию:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("cat_"))
async def show_items(call: types.CallbackQuery):
    cat = call.data[4:]
    data = load_products()
    items = data.get(cat, [])
    if not items:
        return await call.message.answer("Товаров нет.")
    kb = InlineKeyboardMarkup()
    for idx, item in enumerate(items):
        kb.add(InlineKeyboardButton(item, callback_data=f"buy_{cat}_{idx}"))
    await call.message.answer(f"Товары в {cat}:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("buy_"))
async def handle_buy(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(item=call.data)
    await bot.send_message(call.from_user.id, f"💰 Оплатите 700 тг\n📱 Kaspi: {KASPI_NUMBER}\nОтправьте чек сюда (фото)")
    await state.set_state(PurchaseState.waiting_for_payment)

@dp.message_handler(content_types=types.ContentType.ANY, state=PurchaseState.waiting_for_payment)
async def handle_payment(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    await bot.send_message(ADMIN_ID, f"🧾 Чек от @{message.from_user.username or message.from_user.full_name}")
    if message.photo:
        await bot.send_photo(ADMIN_ID, message.photo[-1].file_id)
    elif message.document:
        await bot.send_document(ADMIN_ID, message.document.file_id)
    await bot.send_message(ADMIN_ID, f"Номер жіберу: /send_number {message.from_user.id} <номер>")
    await state.finish()

@dp.message_handler(Command("send_number"), user_id=ADMIN_ID)
async def send_number(message: types.Message):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        return await message.reply("Формат: /send_number <user_id> <номер>")
    user_id = int(parts[1])
    number = parts[2]
    kb = InlineKeyboardMarkup().add(InlineKeyboardButton("🔑 Код алу", callback_data=f"code_request_{user_id}"))
    msg = (f"✅ Номер: {number}\n👤 Иесі: {OWNER_NAME}\n\n"
           "Енді смс кодты алу үшін төмендегі батырманы басыңыз.")
    await bot.send_message(user_id, msg, reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("code_request_"))
async def user_requests_code(call: types.CallbackQuery):
    user_id = call.from_user.id
    await bot.send_message(ADMIN_ID, f"🔐 Код сұрап тұр: @{call.from_user.username or call.from_user.full_name}\nЖіберу үшін: /send_code {user_id} <код>")
    await call.message.edit_reply_markup()  # Remove button

@dp.message_handler(Command("send_code"), user_id=ADMIN_ID)
async def send_sms_code(message: types.Message):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        return await message.reply("Формат: /send_code <user_id> <код>")
    user_id = int(parts[1])
    code = parts[2]
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("✅ Кірдім"), KeyboardButton("❌ Кіре алмадым"))
    await bot.send_message(user_id, f"🔐 Сіздің SMS код: {code}", reply_markup=kb)

@dp.message_handler(lambda m: m.text == "✅ Кірдім")
async def handle_success_login(message: types.Message):
    await message.answer("✍️ Пікір қалдырыңыз, бот туралы ойыңыз біз үшін маңызды!")
    await bot.send_message(ADMIN_ID, f"✅ Кірдім дейді: @{message.from_user.username or message.from_user.full_name}")

@dp.message_handler(lambda m: m.text == "❌ Кіре алмадым")
async def handle_failed_login(message: types.Message):
    await message.answer("⚠️ Кіру мүмкін болмады ма?\nБізге жазыңыз: @renzokzh")
    await bot.send_message(ADMIN_ID, f"❌ Кіре алмадым дейді: @{message.from_user.username or message.from_user.full_name}")

@dp.message_handler(lambda m: m.chat.id != ADMIN_ID)
async def receive_review(message: types.Message):
    await bot.send_message(ADMIN_ID, f"💬 @{message.from_user.username or message.from_user.full_name}:\n{message.text}")

@dp.message_handler(commands=['admin'], user_id=ADMIN_ID)
async def admin_panel(message: types.Message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("➕ Категория"), KeyboardButton("➕ Товар"))
    kb.add(KeyboardButton("🗑 Тауар жою"), KeyboardButton("📦 Категории"))
    await message.answer("🛠 Админ панель:", reply_markup=kb)

@dp.message_handler(text="➕ Категория", user_id=ADMIN_ID)
async def add_category(message: types.Message):
    await message.answer("Категория атын жазыңыз:")
    await PurchaseState.waiting_for_category.set()

@dp.message_handler(state=PurchaseState.waiting_for_category, user_id=ADMIN_ID)
async def save_category(message: types.Message, state: FSMContext):
    data = load_products()
    cat = message.text.strip()
    if cat not in data:
        data[cat] = []
        save_products(data)
        await message.answer(f"✅ Категория '{cat}' қосылды")
    else:
        await message.answer("❗ Категория бұрыннан бар")
    await state.finish()

@dp.message_handler(text="➕ Товар", user_id=ADMIN_ID)
async def ask_category(message: types.Message):
    data = load_products()
    if not data:
        return await message.answer("Категория жоқ")
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for cat in data:
        kb.add(KeyboardButton(cat))
    await message.answer("Қай категорияға қосаңыз?", reply_markup=kb)
    await PurchaseState.waiting_for_category.set()

@dp.message_handler(state=PurchaseState.waiting_for_category, user_id=ADMIN_ID)
async def get_item_name(message: types.Message, state: FSMContext):
    await state.update_data(category=message.text.strip())
    await message.answer("Тауар атын жазыңыз:")
    await PurchaseState.waiting_for_item.set()

@dp.message_handler(state=PurchaseState.waiting_for_item, user_id=ADMIN_ID)
async def save_item(message: types.Message, state: FSMContext):
    data = await state.get_data()
    category = data['category']
    item = message.text.strip()
    products = load_products()
    if category in products:
        products[category].append(item)
        save_products(products)
        await message.answer(f"✅ '{item}' қосылды")
    await state.finish()

@dp.message_handler(text="🗑 Тауар жою", user_id=ADMIN_ID)
async def ask_delete_category(message: types.Message):
    data = load_products()
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for cat in data:
        kb.add(KeyboardButton(cat))
    await message.answer("Қай категориядан тауар жоясыз?", reply_markup=kb)
    await PurchaseState.waiting_for_category.set()

@dp.message_handler(state=PurchaseState.waiting_for_category, user_id=ADMIN_ID)
async def choose_item_to_delete(message: types.Message, state: FSMContext):
    category = message.text.strip()
    products = load_products()
    if category not in products or not products[category]:
        return await message.answer("Тауар жоқ.")
    await state.update_data(category=category)
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for item in products[category]:
        kb.add(KeyboardButton(item))
    await message.answer("Қай тауарды жоясыз?", reply_markup=kb)
    await PurchaseState.waiting_for_item.set()

@dp.message_handler(state=PurchaseState.waiting_for_item, user_id=ADMIN_ID)
async def delete_item(message: types.Message, state: FSMContext):
    data = await state.get_data()
    category = data['category']
    item = message.text.strip()
    products = load_products()
    if item in products[category]:
        products[category].remove(item)
        save_products(products)
        await message.answer(f"🗑 '{item}' жойылды")
    else:
        await message.answer("❗ Тауар табылмады")
    await state.finish()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
