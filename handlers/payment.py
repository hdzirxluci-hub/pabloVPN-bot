from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import select

from database.db import async_session
from database.models import Transaction, User
from utils.keyboards import receipt_review_kb, back_kb
from utils.states import WalletStates
from utils.texts import get_setting, t

router = Router()

@router.callback_query(F.data.startswith("pay:card:"))
async def process_card_pay(callback: CallbackQuery, state: FSMContext):
    amount = int(callback.data.split(":")[2])
    card = await get_setting("card_number", "در حال بروزرسانی")
    holder = await get_setting("card_holder", "پشتیبانی")

    await state.update_data(deposit_amount=amount)
    await state.set_state(WalletStates.waiting_receipt)

    text = t("card_payment_info", amount=amount, card=card, holder=holder)
    await callback.message.answer(text, reply_markup=back_kb())
    await callback.answer()

@router.message(WalletStates.waiting_receipt, F.photo)
async def process_receipt_photo(message: Message, state: FSMContext, bot: Bot):
    photo_id = message.photo[-1].file_id
    data = await state.get_data()
    amount = data.get("deposit_amount", 0)

    async with async_session() as session:
        user_res = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = user_res.scalar_one_or_none()
        if not user:
            return

        tx = Transaction(
            user_id=user.id,
            amount=float(amount),
            type="deposit",
            method="card",
            status="pending",
            receipt_file_id=photo_id
        )
        session.add(tx)
        await session.commit()
        await session.refresh(tx)

    receipt_channel = await get_setting("receipt_channel_id", "")
    if receipt_channel:
        caption = (
            f"🧾 <b>رسید پرداخت جدید #{tx.id}</b>\n\n"
            f"👤 کاربر: <code>{message.from_user.id}</code> (@{message.from_user.username or 'ندارد'})\n"
            f"💰 مبلغ: <b>{amount:,} تومان</b>\n"
            f"💳 روش: کارت به کارت"
        )
        try:
            await bot.send_photo(
                chat_id=receipt_channel,
                photo=photo_id,
                caption=caption,
                reply_markup=receipt_review_kb(tx.id)
            )
        except Exception:
            pass

    await state.clear()
    await message.answer(t("receipt_received"))

@router.callback_query(F.data.startswith("receipt:approve:"))
async def approve_receipt(callback: CallbackQuery, bot: Bot):
    tx_id = int(callback.data.split(":")[2])
    async with async_session() as session:
        res = await session.execute(select(Transaction).where(Transaction.id == tx_id))
        tx = res.scalar_one_or_none()
        if not tx or tx.status != "pending":
            await callback.answer("این رسید قبلا بررسی شده است!", show_alert=True)
            return

        tx.status = "approved"
        user_res = await session.execute(select(User).where(User.id == tx.user_id))
        user = user_res.scalar_one_or_none()
        if user:
            user.balance += tx.amount

        await session.commit()

    if user:
        try:
            await bot.send_message(
                chat_id=user.telegram_id,
                text=t("payment_approved", amount=int(tx.amount))
            )
        except Exception:
            pass

    await callback.message.edit_caption(
        caption=f"{callback.message.caption}\n\n✅ <b>تایید شد توسط: {callback.from_user.first_name}</b>"
    )
    await callback.answer("رسید تایید شد.")