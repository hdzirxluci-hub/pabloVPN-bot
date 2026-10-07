from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select, func

from database.db import async_session
from database.models import User, Service, Transaction
from utils.decorators import owner_only
from utils.keyboards import owner_main_kb, back_kb
from utils.texts import t

router = Router()


class UserMgmtStates(StatesGroup):
    waiting_search = State()
    waiting_action = State()
    waiting_charge_amount = State()
    waiting_ban_reason = State()


@router.message(F.text == "👥 مدیریت کاربران")
@owner_only
async def user_mgmt_menu(message: Message, state: FSMContext):
    async with async_session() as session:
        total = await session.scalar(select(func.count(User.id))) or 0
        banned = await session.scalar(select(func.count(User.id)).where(User.is_banned == True)) or 0
        admins = await session.scalar(select(func.count(User.id)).where(User.is_admin == True)) or 0
    
    await state.set_state(UserMgmtStates.waiting_search)
    await message.answer(
        f"👥 <b>مدیریت کاربران</b>\n\n"
        f"📊 آمار:\n"
        f"• کل کاربران: <code>{total}</code>\n"
        f"• مسدود شده: <code>{banned}</code>\n"
        f"• ادمین‌ها: <code>{admins}</code>\n\n"
        f"🔍 برای جستجوی کاربر، آیدی عددی تلگرام او را بفرستید:",
        reply_markup=back_kb()
    )

@router.message(UserMgmtStates.waiting_search)
@owner_only
async def search_user(message: Message, state: FSMContext):
    if message.text == t("back"):
        await state.clear()
        await message.answer("لغو شد.", reply_markup=owner_main_kb())
        return
    
    if not message.text.strip().isdigit():
        await message.answer("❌ لطفا آیدی عددی وارد کنید.")
        return
    
    tid = int(message.text.strip())
    async with async_session() as session:
        res = await session.execute(select(User).where(User.telegram_id == tid))
        user = res.scalar_one_or_none()
        
        if not user:
            await message.answer("❌ کاربر یافت نشد.")
            return
        
        services_count = await session.scalar(
            select(func.count(Service.id)).where(Service.user_id == user.id)
        ) or 0
        
        purchases = await session.scalar(
            select(func.sum(Transaction.amount)).where(
                Transaction.user_id == user.id,
                Transaction.type == "purchase",
                Transaction.status == "approved"
            )
        ) or 0.0
    
    ban_status = "🚫 مسدود" if user.is_banned else "✅ فعال"
    admin_status = "👑 بله" if user.is_admin else "خیر"
    
    text = (
        f"👤 <b>اطلاعات کاربر</b>\n\n"
        f"🆔 آیدی: <code>{user.telegram_id}</code>\n"
        f"👤 نام: {user.first_name or '-'}\n"
        f"📱 یوزرنیم: @{user.username or '-'}\n"
        f"💰 موجودی: {int(user.balance):,} تومان\n"
        f"📦 تعداد سرویس‌ها: {services_count}\n"
        f"💵 مجموع خرید: {int(purchases):,} تومان\n"
        f"🔒 وضعیت: {ban_status}\n"
        f"🛡️ ادمین: {admin_status}\n"
        f"📅 تاریخ عضویت: {user.joined_at.strftime('%Y/%m/%d')}\n\n"
        f"<b>⚙️ عملیات:</b>\n"
        f"• برای شارژ کیف پول کلمه <code>charge</code> را بفرستید\n"
        f"• برای مسدود کردن کلمه <code>ban</code> را بفرستید\n"
        f"• برای رفع مسدودی کلمه <code>unban</code> را بفرستید\n"
        f"• برای جستجوی کاربر دیگر، آیدی جدید را بفرستید"
    )
    
    await state.update_data(target_user_id=user.telegram_id, target_db_id=user.id)
    await state.set_state(UserMgmtStates.waiting_action)
    await message.answer(text, reply_markup=back_kb())


@router.message(UserMgmtStates.waiting_action)
@owner_only
async def user_action(message: Message, state: FSMContext, bot: Bot):
    if message.text == t("back"):
        await state.clear()
        await message.answer("لغو شد.", reply_markup=owner_main_kb())
        return
    
    text = message.text.strip().lower()
    data = await state.get_data()
    tid = data.get("target_user_id")
    db_id = data.get("target_db_id")
    
    if text == "charge":
        await state.set_state(UserMgmtStates.waiting_charge_amount)
        await message.answer("💰 مبلغ شارژ به تومان را وارد کنید (برای کسر، عدد منفی مثل <code>-5000</code>):")
        return
    
    elif text == "ban":
        async with async_session() as session:
            user = await session.get(User, db_id)
            if user:
                user.is_banned = True
                await session.commit()
        try:
            await bot.send_message(tid, "🚫 شما از ربات مسدود شدید.")
        except Exception:
            pass
        await state.clear()
        await message.answer(f"✅ کاربر {tid} مسدود شد.", reply_markup=owner_main_kb())
        return
    
    elif text == "unban":
        async with async_session() as session:
            user = await session.get(User, db_id)
            if user:
                user.is_banned = False
                await session.commit()
        try:
            await bot.send_message(tid, "✅ مسدودی شما لغو شد.")
        except Exception:
            pass
        await state.clear()
        await message.answer(f"✅ کاربر {tid} رفع مسدودی شد.", reply_markup=owner_main_kb())
        return
    
    elif text.isdigit():
        # جستجوی کاربر جدید
        await state.set_state(UserMgmtStates.waiting_search)
        await search_user(message, state)
        return
    
    else:
        await message.answer("❌ دستور نامعتبر. فقط charge/ban/unban یا آیدی عددی.")


@router.message(UserMgmtStates.waiting_charge_amount)
@owner_only
async def charge_user(message: Message, state: FSMContext, bot: Bot):
    if message.text == t("back"):
        await state.clear()
        await message.answer("لغو شد.", reply_markup=owner_main_kb())
        return
    
    text = message.text.strip().replace(",", "")
    try:
        amount = float(text)
    except ValueError:
        await message.answer("❌ عدد معتبر وارد کنید.")
        return
    
    data = await state.get_data()
    tid = data.get("target_user_id")
    db_id = data.get("target_db_id")
    
    async with async_session() as session:
        user = await session.get(User, db_id)
        if not user:
            await message.answer("❌ کاربر یافت نشد.")
            await state.clear()
            return
        user.balance += amount
        if user.balance < 0:
            user.balance = 0
        await session.commit()
        new_balance = user.balance
    
    try:
        action = "اضافه" if amount >= 0 else "کسر"
        await bot.send_message(
            tid,
            f"💰 مبلغ {int(abs(amount)):,} تومان از کیف پول شما {action} شد.\n"
            f"موجودی جدید: {int(new_balance):,} تومان"
        )
    except Exception:
        pass
    
    await state.clear()
    await message.answer(
        f"✅ موجودی کاربر {tid} به {int(new_balance):,} تومان رسید.",
        reply_markup=owner_main_kb()
    )