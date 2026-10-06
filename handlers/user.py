from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select

from database.db import async_session
from database.models import Service, User, Plan, Setting
from utils.helpers import is_owner, is_admin, format_date, format_bytes
from utils.keyboards import main_menu_kb, services_kb
from utils.texts import format_text, get_setting, t

router = Router()

@router.message(F.text == t("back"))
@router.message(F.text == t("cancel"))
async def back_to_main(message: Message, state: FSMContext):
    await state.clear()
    owner_flag = await is_owner(message.from_user.id)
    admin_flag = await is_admin(message.from_user.id)
    await message.answer(
        t("main_menu"),
        reply_markup=main_menu_kb(is_owner=owner_flag, is_admin=admin_flag)
    )

@router.message(F.text == t("user_menu_about"))
async def about_us(message: Message):
    text = await format_text("about_text", "🚀 درباره ما")
    await message.answer(text)

@router.message(F.text == t("user_menu_rules"))
async def bot_rules(message: Message):
    text = await get_setting("rules_text", "📜 قوانین ربات...")
    await message.answer(text)

@router.message(F.text == t("user_menu_guide"))
async def connection_guide(message: Message):
    guide_text = (
        "📚 <b>راهنمای اتصال به VPN</b>\n\n"
        "📱 <b>اندروید:</b> برنامه v2rayNG یا Happ را از گوگل پلی دانلود کنید.\n"
        "🍏 <b>آیفون (iOS):</b> برنامه V2Box, Streisand یا FoXray را از اپ‌استور دانلود کنید.\n"
        "💻 <b>ویندوز:</b> برنامه v2rayN یا Nekoray را دانلود کنید.\n\n"
        "💡 پس از خرید، لینک اختصاصی را در برنامه Import نمایید."
    )
    await message.answer(guide_text)

@router.message(F.text == t("user_menu_services"))
async def my_services(message: Message):
    async with async_session() as session:
        user_res = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = user_res.scalar_one_or_none()
        if not user:
            return

        srv_res = await session.execute(
            select(Service).where(Service.user_id == user.id, Service.is_active == True)
        )
        services = srv_res.scalars().all()

    if not services:
        await message.answer(t("no_services"))
        return

    await message.answer("📦 لیست سرویس‌های فعال شما:", reply_markup=services_kb(services))

@router.callback_query(F.data.startswith("srv:"))
async def service_details(callback: CallbackQuery):
    srv_id = int(callback.data.split(":")[1])
    async with async_session() as session:
        res = await session.execute(select(Service).where(Service.id == srv_id))
        srv = res.scalar_one_or_none()

    if not srv:
        await callback.answer("سرویس یافت نشد!", show_alert=True)
        return

    text = t(
        "service_info",
        name=srv.username,
        traffic=srv.traffic_gb,
        days=srv.duration_days,
        expires=format_date(srv.expires_at),
        link=srv.subscription_url or srv.config_data or "نامشخص"
    )
    await callback.message.answer(text)
    await callback.answer()