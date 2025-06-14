import json
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Command
import logging
from aiogram.types import InputFile

TOKEN = "7838676161:AAHt0qJoMwcezd_b1IHKUSAWjBsI2t9qpdw"
ADMIN_ID = 8100416617
KASPI_NUMBER = "+7 708 602 4478"
OWNER_NAME = "Раушангул.Б"
PRODUCT_FILE = "products.json"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

class AddCategory(StatesGroup):
    waiting_for_category = State()

class AddProduct(StatesGroup):
    waiting_for_cat = State()
    waiting_for_name = State()
    waiting_for_price = State()

class EditProduct(StatesGroup):
    waiting_for_cat = State()
    waiting_for_index = State()
    waiting_for_new_value = State()

class DeleteProduct(StatesGroup):
    waiting_for_cat = State()
    waiting_for_index = State()

class Purchase(StatesGroup):
    waiting_for_payment = State()
    waiting_for_code_request = State()

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
        return await message.answer("Категорий жоқ.")
    kb = InlineKeyboardMarkup()
    for cat in data:
        kb.add(InlineKeyboardButton(f"{cat} ({len(data[cat])})", callback_data=f"cat_{cat}"))
    await message.answer("Категорияны таңдаңыз:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("cat_"))
async def show_items(call: types.CallbackQuery):
    cat = call.data.split("_", 1)[1]
    data = load_products()
    items = data.get(cat, [])
    if not items:
        return await call.message.answer("Бұл категорияда тауар жоқ.")
    kb = InlineKeyboardMarkup()
    for i, item in enumerate(items):
        kb.add(InlineKeyboardButton(f"{item['name']} ({item['price']}тг)", callback_data=f"buy_{cat}_{i}"))
    await call.message.answer(f"{cat} ішіндегі тауарлар:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("buy_"))
async def handle_buy(call: types.CallbackQuery, state: FSMContext):
    _, cat, index = call.data.split("_")
    data = load_products()
    item = data[cat][int(index)]
    await state.update_data(category=cat, index=index, item=item)
    await call.message.answer(f"💰 {item['name']} бағасы: {item['price']} тг\nKaspi: {KASPI_NUMBER}\nЧек жіберіңіз:")
    await state.set_state(Purchase.waiting_for_payment)

@dp.message_handler(content_types=types.ContentType.ANY, state=Purchase.waiting_for_payment)
async def handle_payment(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    item = user_data['item']
    await bot.send_message(ADMIN_ID, f"📥 @{message.from_user.username or message.from_user.full_name} чек жіберді.\nТауар: {item['name']} ({item['price']} тг)")
    if message.photo:
        await bot.send_photo(ADMIN_ID, message.photo[-1].file_id)
    elif message.document:
        await bot.send_document(ADMIN_ID, message.document.file_id)
    await bot.send_message(ADMIN_ID, f"Осы қолданушыға номер жіберіңіз:\n/send_number {message.from_user.id} <номер>")
    await state.finish()

@dp.message_handler(Command("send_number"), user_id=ADMIN_ID)
async def send_number(message: types.Message):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        return await message.reply("Қате формат: /send_number <user_id> <номер>")
    user_id = int(parts[1])
    number = parts[2]
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("🔑 Код алу"))
    await bot.send_message(user_id,
        f"📱 Номеріңіз: {number}\n👤 Иесі: {OWNER_NAME}\n\n❗ Есіңізде болсын:\n- Құпиясөзді өзгертіңіз\n- Қос факторлы қорғауды қосыңыз",
        reply_markup=kb)

@dp.message_handler(text="🔑 Код алу")
async def ask_code(message: types.Message):
    await bot.send_message(ADMIN_ID, f"⚠️ @{message.from_user.username or message.from_user.full_name} код сұрап жатыр.\nЖіберіңіз: /send_code {message.from_user.id} <код>")
    await message.answer("✅ Админге хабар жіберілді. Күтіңіз...")

@dp.message_handler(Command("send_code"), user_id=ADMIN_ID)
async def send_sms_code(message: types.Message):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        return await message.reply("Қате формат: /send_code <user_id> <код>")
    user_id = int(parts[1])
    code = parts[2]
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("✅ Кірдім"), KeyboardButton("❌ Кіре алмадым"))
    await bot.send_message(user_id, f"🔑 Сіздің кодыңыз: {code}", reply_markup=kb)

@dp.message_handler(text="✅ Кірдім")
async def success_login(message: types.Message):
    await message.answer("🙏 Рақмет! Пікір қалдыруыңызды сұраймыз.")
    await bot.send_message(ADMIN_ID, f"✅ @{message.from_user.username} сәтті кірді.")
    
@dp.message_handler(text="❌ Кіре алмадым")
async def failed_login(message: types.Message):
    await message.answer("Қиындық болса, @renzokzh профиліне жазыңыз.")

# --- Отзывтар ---
@dp.message_handler(lambda m: m.chat.id != ADMIN_ID)
async def review(message: types.Message):
    await bot.send_message(ADMIN_ID, f"💬 @{message.from_user.username or message.from_user.full_name} пікірі:\n{message.text}")

# --- Админ панель ---
@dp.message_handler(commands=['admin'], user_id=ADMIN_ID)
async def admin(message: types.Message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("➕ Категория"), KeyboardButton("➕ Товар"))
    kb.add(KeyboardButton("🗑 Тауарды өшіру"), KeyboardButton("✏️ Тауарды өзгерту"))
    await message.answer("Админ панелі:", reply_markup=kb)

@dp.message_handler(text="➕ Категория", user_id=ADMIN_ID)
async def add_cat_start(message: types.Message):
    await message.answer("Жаңа категория атауын жазыңыз:")
    await AddCategory.waiting_for_category.set()

@dp.message_handler(state=AddCategory.waiting_for_category, user_id=ADMIN_ID)
async def add_cat_save(message: types.Message, state: FSMContext):
    data = load_products()
    cat = message.text.strip()
    if cat not in data:
        data[cat] = []
        save_products(data)
        await message.answer("✅ Категория қосылды")
    else:
        await message.answer("❗ Категория бұрыннан бар")
    await state.finish()

@dp.message_handler(text="➕ Товар", user_id=ADMIN_ID)
async def add_prod_start(message: types.Message):
    await message.answer("Категория атауын жазыңыз:")
    await AddProduct.waiting_for_cat.set()

@dp.message_handler(state=AddProduct.waiting_for_cat, user_id=ADMIN_ID)
async def add_prod_cat(message: types.Message, state: FSMContext):
    await state.update_data(category=message.text.strip())
    await message.answer("Тауар атауын жазыңыз:")
    await AddProduct.waiting_for_name.set()

@dp.message_handler(state=AddProduct.waiting_for_name, user_id=ADMIN_ID)
async def add_prod_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer("Бағасын жазыңыз (тек сан):")
    await AddProduct.waiting_for_price.set()

@dp.message_handler(state=AddProduct.waiting_for_price, user_id=ADMIN_ID)
async def add_prod_price(message: types.Message, state: FSMContext):
    data = await state.get_data()
    cat, name, price = data["category"], data["name"], message.text.strip()
    products = load_products()
    if cat in products:
        products[cat].append({"name": name, "price": price})
        save_products(products)
        await message.answer("✅ Тауар қосылды")
    else:
        await message.answer("❗ Категория табылмады")
    await state.finish()

@dp.message_handler(text="🗑 Тауарды өшіру", user_id=ADMIN_ID)
async def delete_product_start(message: types.Message):
    await message.answer("Категория атауын жазыңыз:")
    await DeleteProduct.waiting_for_cat.set()

@dp.message_handler(state=DeleteProduct.waiting_for_cat, user_id=ADMIN_ID)
async def delete_prod_cat(message: types.Message, state: FSMContext):
    await state.update_data(category=message.text.strip())
    await message.answer("Қай индекс (0, 1, 2...) тауарды өшіру керек?")
    await DeleteProduct.waiting_for_index.set()

@dp.message_handler(state=DeleteProduct.waiting_for_index, user_id=ADMIN_ID)
async def delete_prod_done(message: types.Message, state: FSMContext):
    data = await state.get_data()
    cat, index = data["category"], int(message.text.strip())
    products = load_products()
    if cat in products and 0 <= index < len(products[cat]):
        deleted = products[cat].pop(index)
        save_products(products)
        await message.answer(f"✅ Өшірілді: {deleted['name']}")
    else:
        await message.answer("❗ Қате индекс немесе категория")
    await state.finish()

# --- START ---
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
