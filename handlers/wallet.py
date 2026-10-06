from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import select

from database.db import async_session
from database.models import User
from utils.keyboards import payment_methods_kb, back_kb, main_menu_kb
from utils.states import WalletStates
from utils.texts import get_setting, t

router = Router()

@router.message(F.text == t("user_menu_wallet"))
async def show_wallet(message: Message):
    async with async_session() as session:
        res = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
        user = res.scalar_one_or_none()
        balance = user.balance if user else 0.0

    text = t("wallet_balance", balance=int(balance))
    await message.answer(text)
    await message.answer("برای افزایش موجودی، لطفا مبلغ مورد نظر را به تومان وارد کنید:", reply_markup=back_kb())

@router.message(F.text.isdigit())
async def handle_charge_amount(message: Message, state: FSMContext):
    amount = int(message.text.strip())
    min_charge = int(await get_setting("min_wallet_charge", "10000"))
    max_charge = int(await get_setting("max_wallet_charge", "10000000"))

    if amount < min_charge:
        await message.answer(t("amount_too_low", min=min_charge))
        return
    if amount > max_charge:
        await message.answer(t("amount_too_high", max=max_charge))
        return

    methods_str = await get_setting("payment_methods", "card")
    methods = [m.strip() for m in methods_str.split(",")]

    await message.answer(
        f"مبلغ انتخابی: <b>{amount:,} تومان</b>\n\nلطفا روش پرداخت را انتخاب کنید:",
        reply_markup=payment_methods_kb(methods, amount)
    )