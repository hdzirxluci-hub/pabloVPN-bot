from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import select

from database.db import async_session
from database.models import User
from utils.decorators import admin_only
from utils.helpers import is_owner
from utils.keyboards import admin_main_kb
from utils.states import AdminStates
from utils.texts import t

router = Router()

@router.message(F.text == t("admin_menu"))
@admin_only
async def admin_dashboard(message: Message, state: FSMContext):
    await state.clear()
    perms = ["all"] if await is_owner(message.from_user.id) else ["receipts", "tickets", "wallet_charge", "stats"]
    await message.answer("🛡️ به پنل ادمین خوش آمدید.", reply_markup=admin_main_kb(perms))

@router.message(F.text == "💰 شارژ کیف پول")
@admin_only
async def manual_charge_prompt(message: Message, state: FSMContext):
    await state.set_state(AdminStates.waiting_charge_user_id)
    await message.answer("آیدی عددی تلگرام کاربر را وارد کنید:")

@router.message(AdminStates.waiting_charge_user_id)
@admin_only
async def manual_charge_user(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ لطفا یک آیدی عددی معتبر ارسال کنید.")
        return
    await state.update_data(target_user_id=int(message.text.strip()))
    await state.set_state(AdminStates.waiting_charge_amount)
    await message.answer("مبلغ شارژ را به تومان وارد کنید:")

@router.message(AdminStates.waiting_charge_amount)
@admin_only
async def manual_charge_amount(message: Message, state: FSMContext):
    amount_str = message.text.strip().replace(",", "")
    if not amount_str.isdigit():
        await message.answer("❌ لطفا یک مبلغ معتبر وارد کنید.")
        return
    amount = float(amount_str)
    data = await state.get_data()
    target_id = data["target_user_id"]

    async with async_session() as session:
        res = await session.execute(select(User).where(User.telegram_id == target_id))
        user = res.scalar_one_or_none()
        if not user:
            await message.answer("❌ کاربر در دیتابیس یافت نشد.")
            await state.clear()
            return
        user.balance += amount
        await session.commit()

    await state.clear()
    await message.answer(f"✅ مبلغ {int(amount):,} تومان با موفقیت به حساب کاربر {target_id} اضافه شد.")