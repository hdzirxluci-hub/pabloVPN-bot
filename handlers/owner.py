from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, func

from config import config
from database.db import async_session
from database.models import User, Panel, Plan, Setting, Transaction, ForcedChannel
from utils.decorators import owner_only
from utils.keyboards import owner_main_kb, back_kb
from utils.states import OwnerStates
from utils.texts import set_setting, get_setting, clear_cache, t

router = Router()

@router.message(F.text == t("owner_menu"))
@owner_only
async def owner_dashboard(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("👑 به پنل مدیریت مالک خوش آمدید.", reply_markup=owner_main_kb())

@router.message(F.text == "📊 آمار ربات")
@owner_only
async def bot_statistics(message: Message):
    async with async_session() as session:
        users_count = await session.scalar(select(func.count(User.id)))
        sales_sum = await session.scalar(
            select(func.sum(Transaction.amount)).where(
                Transaction.type == "purchase",
                Transaction.status == "approved"
            )
        ) or 0.0
        active_panels = await session.scalar(
            select(func.count(Panel.id)).where(Panel.is_active == True)
        )

    text = (
        "📊 <b>آمار و وضعیت PabloVPN</b>\n\n"
        f"👥 کل کاربران: <code>{users_count}</code> نفر\n"
        f"💰 کل فروش: <code>{int(sales_sum):,}</code> تومان\n"
        f"🔌 پنل‌های متصل و فعال: <code>{active_panels}</code>\n"
    )
    await message.answer(text)

@router.message(F.text == "🎨 برندینگ و متن‌ها")
@owner_only
async def branding_menu(message: Message, state: FSMContext):
    await state.set_state(OwnerStates.waiting_brand_name)
    brand = await get_setting("brand_name", "PabloVPN")
    await message.answer(
        f"نام فعلی برند: <b>{brand}</b>\n\nلطفا نام جدید برند را ارسال کنید یا دکمه بازگشت را بزنید:",
        reply_markup=back_kb()
    )

@router.message(OwnerStates.waiting_brand_name)
@owner_only
async def save_brand_name(message: Message, state: FSMContext):
    if message.text == t("back"):
        await state.clear()
        await message.answer("عملیات لغو شد.", reply_markup=owner_main_kb())
        return
    await set_setting("brand_name", message.text.strip())
    clear_cache()
    await state.clear()
    await message.answer(f"✅ نام برند به <b>{message.text.strip()}</b> تغییر یافت.", reply_markup=owner_main_kb())

@router.message(F.text == "💳 تنظیمات پرداخت")
@owner_only
async def payment_settings(message: Message, state: FSMContext):
    card = await get_setting("card_number", "تنظیم نشده")
    holder = await get_setting("card_holder", "تنظیم نشده")
    await state.set_state(OwnerStates.waiting_card_number)
    await message.answer(
        f"💳 <b>تنظیمات کارت بانکی</b>\n\nشماره کارت فعلی: <code>{card}</code>\nصاحب حساب: <b>{holder}</b>\n\nلطفا شماره کارت ۱۶ رقمی جدید را بفرستید:",
        reply_markup=back_kb()
    )

@router.message(OwnerStates.waiting_card_number)
@owner_only
async def save_card_number(message: Message, state: FSMContext):
    if message.text == t("back"):
        await state.clear()
        await message.answer("لغو شد.", reply_markup=owner_main_kb())
        return
    await state.update_data(card_number=message.text.strip())
    await state.set_state(OwnerStates.waiting_card_holder)
    await message.answer("👤 لطفا نام صاحب حساب را ارسال کنید:")

@router.message(OwnerStates.waiting_card_holder)
@owner_only
async def save_card_holder(message: Message, state: FSMContext):
    data = await state.get_data()
    card_number = data.get("card_number")
    holder = message.text.strip()
    await set_setting("card_number", card_number)
    await set_setting("card_holder", holder)
    clear_cache()
    await state.clear()
    await message.answer("✅ مشخصات کارت بانکی با موفقیت ثبت شد.", reply_markup=owner_main_kb())

@router.message(F.text == "🔌 مدیریت پنل‌ها")
@owner_only
async def panels_list(message: Message, state: FSMContext):
    await state.set_state(OwnerStates.waiting_panel_name)
    await message.answer(
        "🔌 <b>افزودن پنل VPN جدید</b>\n\nلطفا یک نام برای پنل وارد کنید (مثلا: Marzban-Germany):",
        reply_markup=back_kb()
    )

@router.message(OwnerStates.waiting_panel_name)
@owner_only
async def panel_name_step(message: Message, state: FSMContext):
    if message.text == t("back"):
        await state.clear()
        await message.answer("لغو شد.", reply_markup=owner_main_kb())
        return
    await state.update_data(name=message.text.strip())
    await state.set_state(OwnerStates.waiting_panel_type)
    await message.answer("نوع پنل را ارسال کنید:\n(marzban, 3xui, sanaei, pasargad)")

@router.message(OwnerStates.waiting_panel_type)
@owner_only
async def panel_type_step(message: Message, state: FSMContext):
    ptype = message.text.strip().lower()
    if ptype not in ["marzban", "3xui", "sanaei", "pasargad"]:
        await message.answer("❌ نامعتبر است! یکی از موارد: marzban, 3xui, sanaei, pasargad")
        return
    await state.update_data(panel_type=ptype)
    await state.set_state(OwnerStates.waiting_panel_url)
    await message.answer("🔗 آدرس URL پنل با پورت را بفرستید (مثال: https://panel.site.com:8000):")

@router.message(OwnerStates.waiting_panel_url)
@owner_only
async def panel_url_step(message: Message, state: FSMContext):
    await state.update_data(url=message.text.strip().rstrip("/"))
    await state.set_state(OwnerStates.waiting_panel_username)
    await message.answer("👤 نام کاربری ادمین پنل را وارد کنید:")

@router.message(OwnerStates.waiting_panel_username)
@owner_only
async def panel_username_step(message: Message, state: FSMContext):
    await state.update_data(username=message.text.strip())
    await state.set_state(OwnerStates.waiting_panel_password)
    await message.answer("🔑 رمز عبور ادمین پنل را وارد کنید:")

@router.message(OwnerStates.waiting_panel_password)
@owner_only
async def panel_password_step(message: Message, state: FSMContext):
    data = await state.get_data()
    async with async_session() as session:
        panel = Panel(
            name=data["name"],
            panel_type=data["panel_type"],
            url=data["url"],
            username=data["username"],
            password=message.text.strip()
        )
        session.add(panel)
        await session.commit()
    await state.clear()
    await message.answer("✅ پنل با موفقیت به ربات متصل شد.", reply_markup=owner_main_kb())

@router.message(F.text == "📣 ارسال همگانی")
@owner_only
async def broadcast_prompt(message: Message, state: FSMContext):
    await state.set_state(OwnerStates.waiting_broadcast)
    await message.answer("✍️ پیام همگانی خود را ارسال کنید:", reply_markup=back_kb())

@router.message(OwnerStates.waiting_broadcast)
@owner_only
async def broadcast_send(message: Message, state: FSMContext, bot: Bot):
    if message.text == t("back"):
        await state.clear()
        await message.answer("لغو شد.", reply_markup=owner_main_kb())
        return
    async with async_session() as session:
        users = (await session.execute(select(User.telegram_id))).scalars().all()

    success, failed = 0, 0
    await message.answer("⏳ در حال ارسال پیام به تمام کاربران...")
    for uid in users:
        try:
            await bot.copy_message(chat_id=uid, from_chat_id=message.chat.id, message_id=message.message_id)
            success += 1
        except Exception:
            failed += 1

    await state.clear()
    await message.answer(
        f"✅ ارسال همگانی پایان یافت.\n\n✔️ موفق: {success}\n❌ ناموفق: {failed}",
        reply_markup=owner_main_kb()
    )