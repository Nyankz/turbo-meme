from aiogram import Bot
from config import CHANNEL_ID
from database import battles
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()
bot: Bot = None  # Кейін main-нан орнатамыз

def init_scheduler(bot_instance):
    global bot
    bot = bot_instance
    scheduler.start()

async def finish_battle(battle_id):
    battle = battles.get(battle_id)
    if not battle:
        return

    votes = battle['votes']
    user1 = battle['user1']
    user2 = battle['user2']
    count1 = list(votes.values()).count(user1['id'])
    count2 = list(votes.values()).count(user2['id'])

    if count1 > count2:
        winner = user1
    elif count2 > count1:
        winner = user2
    else:
        winner = None

    result = f"⏰ Battle аяқталды!\n\n"
    result += f"{user1['name']}: {count1} дауыс\n{user2['name']}: {count2} дауыс\n\n"

    if winner:
        result += f"🏆 ЖЕҢІМПАЗ: {winner['name']}!"
    else:
        result += "⚔️ ТЕҢ БОЛДЫ!"

    await bot.send_message(CHANNEL_ID, result)
    del battles[battle_id]