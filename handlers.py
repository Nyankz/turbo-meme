from aiogram import Router, F
from aiogram.types import (
    Message, BufferedInputFile, InlineKeyboardMarkup,
    InlineKeyboardButton, CallbackQuery
)
from aiogram.enums import ContentType
from io import BytesIO
from PIL import Image
import asyncio
from datetime import datetime, timedelta
from config import CHANNEL_ID

router = Router()

waiting_users = []
votes = {"1": 0, "2": 0}
voted_users = set()

@router.message(F.content_type.in_([ContentType.PHOTO]))
async def photo_handler(message: Message):
    await message.answer("Атыңды жаз:")
    photo = await message.bot.download(message.photo[-1])

    waiting_users.append({
        'user_id': message.from_user.id,
        'photo': photo,
        'name': None,
        'message': message
    })

@router.message(F.text)
async def name_handler(message: Message):
    user = next((u for u in waiting_users if u['user_id'] == message.from_user.id and u['name'] is None), None)
    if not user:
        return

    user['name'] = message.text.strip()

    ready_users = [u for u in waiting_users if u['name']]
    if len(ready_users) >= 2:
        user1 = ready_users.pop(0)
        user2 = ready_users.pop(0)
        for u in (user1, user2):
            waiting_users.remove(u)

        await start_battle(user1, user2, message.bot)

async def start_battle(user1, user2, bot):
    global votes, voted_users
    votes = {"1": 0, "2": 0}
    voted_users = set()

    img1 = Image.open(user1['photo']).resize((512, 512))
    img2 = Image.open(user2['photo']).resize((512, 512))

    combined = Image.new("RGB", (1024, 512))
    combined.paste(img1, (0, 0))
    combined.paste(img2, (512, 0))

    buf = BytesIO()
    combined.save(buf, format='JPEG')
    buf.seek(0)
    input_photo = BufferedInputFile(buf.getvalue(), filename="battle.jpg")

    now = datetime.now()
    end = now + timedelta(minutes=30)
    time_range = f"🕒 Уақыт: {now.strftime('%H:%M')} - {end.strftime('%H:%M')} (Алматы)"

    caption = (
        f"1. {user1['name']}\n"
        f"2. {user2['name']}\n\n"
        f"{time_range}\n\n"
        "❤️ Кім ұнайды, соған дауыс бер 👇"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"1. {user1['name']} (0)", callback_data="vote_1")],
        [InlineKeyboardButton(text=f"2. {user2['name']} (0)", callback_data="vote_2")]
    ])

    post = await bot.send_photo(
        chat_id=CHANNEL_ID,
        photo=input_photo,
        caption=caption,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await bot.send_message(user1['user_id'], "🎉 Сізге жұп табылды! Каналды тексеріңіз.")
    await bot.send_message(user2['user_id'], "🎉 Сізге жұп табылды! Каналды тексеріңіз.")

    asyncio.create_task(end_battle(post, user1['name'], user2['name'], bot))

@router.callback_query(F.data.startswith("vote_"))
async def handle_vote(call: CallbackQuery):
    global votes, voted_users

    if call.from_user.id in voted_users:
        await call.answer("Сіз бұрында дауыс бердіңіз!", show_alert=True)
        return

    voted_users.add(call.from_user.id)
    vote = call.data.split("_")[1]
    if vote in votes:
        votes[vote] += 1

    new_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"1. ({votes['1']})", callback_data="vote_1")],
        [InlineKeyboardButton(text=f"2. ({votes['2']})", callback_data="vote_2")]
    ])
    await call.message.edit_reply_markup(reply_markup=new_markup)
    await call.answer("✅ Дауыс берілді")

async def end_battle(msg, name1, name2, bot):
    await asyncio.sleep(1800)  # 30 минут күту

    result = ""
    if votes['1'] > votes['2']:
        result = f"🥇 Жеңімпаз: {name1} ({votes['1']} дауыс)"
    elif votes['2'] > votes['1']:
        result = f"🥇 Жеңімпаз: {name2} ({votes['2']} дауыс)"
    else:
        result = "⚔️ Екеуі тең түсті!"

    await msg.edit_caption(msg.caption + f"\n\n{result}")

