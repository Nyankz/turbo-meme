from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database import get_battle_votes
from config import CHANNEL_ID
from aiogram import Bot

scheduler = AsyncIOScheduler()

def schedule_battle_end(bot: Bot, battle_id: str, end_time):
    scheduler.add_job(end_battle, "date", run_date=end_time, args=[bot, battle_id])

async def end_battle(bot: Bot, battle_id: str):
    votes = get_battle_votes(battle_id)
    if not votes:
        winner = "❌ Дауыс берілмеді"
    else:
        winner = max(votes, key=votes.get)
        count = votes[winner]
        winner = f"🏆 Жеңімпаз: {winner} ({count} дауыс)"

    await bot.send_message(CHANNEL_ID, f"🕒 Батл аяқталды!\n{winner}")