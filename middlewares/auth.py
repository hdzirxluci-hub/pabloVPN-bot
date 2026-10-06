from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from sqlalchemy import select

from config import config
from database.db import async_session
from database.models import User, ForcedChannel, Setting
from utils.helpers import get_or_create_user
from utils.keyboards import forced_join_kb
from utils.texts import t

class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user_tg = None
        bot = data.get("bot")

        if isinstance(event, Message):
            user_tg = event.from_user
        elif isinstance(event, CallbackQuery):
            user_tg = event.from_user

        if not user_tg:
            return await handler(event, data)

        db_user = await get_or_create_user(
            telegram_id=user_tg.id,
            username=user_tg.username,
            first_name=user_tg.first_name
        )

        data["db_user"] = db_user

        if db_user.is_banned and user_tg.id != config.OWNER_ID:
            if isinstance(event, Message):
                await event.answer(t("banned"))
            elif isinstance(event, CallbackQuery):
                await event.answer(t("banned"), show_alert=True)
            return

        if user_tg.id == config.OWNER_ID:
            return await handler(event, data)

        # بررسی عضویت اجباری
        if isinstance(event, Message) and event.text and event.text.startswith("/start"):
            pass
        elif isinstance(event, CallbackQuery) and event.data == "check_join":
            pass
        else:
            async with async_session() as session:
                setting_res = await session.execute(
                    select(Setting).where(Setting.key == "channel_lock_enabled")
                )
                lock_setting = setting_res.scalar_one_or_none()
                is_lock_enabled = lock_setting.value == "1" if lock_setting else False

                if is_lock_enabled and bot:
                    ch_res = await session.execute(
                        select(ForcedChannel).where(ForcedChannel.is_active == True)
                    )
                    channels = ch_res.scalars().all()
                    not_joined = []
                    for ch in channels:
                        try:
                            member = await bot.get_chat_member(chat_id=ch.channel_id, user_id=user_tg.id)
                            if member.status in ["left", "kicked"]:
                                not_joined.append(ch)
                        except Exception:
                            continue

                    if not_joined:
                        text = t("join_required")
                        kb = forced_join_kb(not_joined)
                        if isinstance(event, Message):
                            await event.answer(text, reply_markup=kb)
                        elif isinstance(event, CallbackQuery):
                            await event.message.answer(text, reply_markup=kb)
                        return

        return await handler(event, data)