from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from sqlalchemy import select

from database.db import async_session
from database.models import User, ForcedChannel, Setting
from utils.helpers import get_or_create_user, is_owner, is_admin, extract_referrer_from_start
from utils.keyboards import main_menu_kb, forced_join_kb
from utils.texts import format_text, t

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject, state: FSMContext):
    await state.clear()
    referrer_id = None
    if command.args:
        referrer_id = extract_referrer_from_start(command.args)

    user = await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        referrer_id=referrer_id
    )

    owner_flag = await is_owner(message.from_user.id)
    admin_flag = await is_admin(message.from_user.id)

    async with async_session() as session:
        trial_setting = await session.execute(
            select(Setting).where(Setting.key == "free_trial_enabled")
        )
        row = trial_setting.scalar_one_or_none()
        trial_enabled = (row.value == "1") if row else False
        show_trial = trial_enabled and not user.free_trial_used

    welcome_msg = await format_text("welcome_text", "🌟 به {brand} خوش آمدید!")
    kb = main_menu_kb(is_owner=owner_flag, is_admin=admin_flag, show_trial=show_trial)
    await message.answer(welcome_msg, reply_markup=kb)

@router.callback_query(F.data == "check_join")
async def check_membership(callback: CallbackQuery, bot: Bot):
    async with async_session() as session:
        ch_res = await session.execute(
            select(ForcedChannel).where(ForcedChannel.is_active == True)
        )
        channels = ch_res.scalars().all()
        not_joined = []
        for ch in channels:
            try:
                member = await bot.get_chat_member(chat_id=ch.channel_id, user_id=callback.from_user.id)
                if member.status in ["left", "kicked"]:
                    not_joined.append(ch)
            except Exception:
                continue

    if not_joined:
        await callback.answer(t("not_joined"), show_alert=True)
    else:
        await callback.message.delete()
        owner_flag = await is_owner(callback.from_user.id)
        admin_flag = await is_admin(callback.from_user.id)
        welcome_msg = await format_text("welcome_text", "🌟 به {brand} خوش آمدید!")
        await callback.message.answer(
            welcome_msg,
            reply_markup=main_menu_kb(is_owner=owner_flag, is_admin=admin_flag)
        )