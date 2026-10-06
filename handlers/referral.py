from aiogram import Router, F, Bot
from aiogram.types import Message
from sqlalchemy import select, func

from database.db import async_session
from database.models import User
from utils.texts import get_setting, t

router = Router()

@router.message(F.text == t("user_menu_referral"))
async def referral_dashboard(message: Message, bot: Bot):
    bot_me = await bot.get_me()
    ref_link = f"https://t.me/{bot_me.username}?start=ref_{message.from_user.id}"

    async with async_session() as session:
        res = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = res.scalar_one_or_none()

        refs_count = await session.scalar(
            select(func.count(User.id)).where(User.referrer_id == message.from_user.id)
        ) or 0

    percent = await get_setting("referral_percent", "10")
    earnings = user.referral_earnings if user else 0.0

    text = t(
        "referral_info",
        link=ref_link,
        count=refs_count,
        earnings=int(earnings),
        percent=percent
    )
    await message.answer(text)