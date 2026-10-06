from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select

from database.db import async_session
from database.models import DiscountCode, DiscountUsage, User
from utils.decorators import owner_only
from utils.keyboards import owner_main_kb, back_kb
from utils.states import OwnerStates
from utils.helpers import generate_random_string
from utils.texts import t

router = Router()

@router.message(F.text == "🎁 زیرمجموعه و تخفیف")
@owner_only
async def discount_menu(message: Message, state: FSMContext):
    await state.set_state(OwnerStates.waiting_discount_code)
    await message.answer(
        "🏷️ <b>ایجاد کد تخفیف جدید</b>\n\nکد تخفیف دلخواه را وارد کنید (مثلا: PABLO50) یا کلمه <code>auto</code> را بفرستید تا خودکار ساخته شود:",
        reply_markup=back_kb()
    )

@router.message(OwnerStates.waiting_discount_code)
@owner_only
async def discount_code_step(message: Message, state: FSMContext):
    if message.text == t("back"):
        await state.clear()
        await message.answer("لغو شد.", reply_markup=owner_main_kb())
        return

    code = message.text.strip().upper()
    if code == "AUTO":
        code = f"PABLO{generate_random_string(6).upper()}"

    async with async_session() as session:
        exists = await session.execute(select(DiscountCode).where(DiscountCode.code == code))
        if exists.scalar_one_or_none():
            await message.answer("❌ این کد قبلا ثبت شده! کد دیگری انتخاب کنید.")
            return

    await state.update_data(discount_code=code)
    await state.set_state(OwnerStates.waiting_discount_percent)
    await message.answer(f"کد: <code>{code}</code>\n\nحالا درصد تخفیف را وارد کنید (مثلا 20):")

@router.message(OwnerStates.waiting_discount_percent)
@owner_only
async def discount_percent_step(message: Message, state: FSMContext):
    if not message.text.isdigit() or not (1 <= int(message.text) <= 100):
        await message.answer("❌ عدد بین ۱ تا ۱۰۰ وارد کنید.")
        return
    await state.update_data(discount_percent=int(message.text))
    await state.set_state(OwnerStates.waiting_discount_uses)
    await message.answer("حداکثر تعداد استفاده از این کد را وارد کنید (برای نامحدود عدد 0 را بفرستید):")

@router.message(OwnerStates.waiting_discount_uses)
@owner_only
async def discount_uses_step(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ لطفا یک عدد صحیح وارد کنید.")
        return
    data = await state.get_data()
    async with async_session() as session:
        dc = DiscountCode(
            code=data["discount_code"],
            percent=data["discount_percent"],
            max_uses=int(message.text),
            is_active=True
        )
        session.add(dc)
        await session.commit()
    await state.clear()
    await message.answer(
        f"✅ کد تخفیف <code>{data['discount_code']}</code> با {data['discount_percent']}% تخفیف ساخته شد.",
        reply_markup=owner_main_kb()
    )

async def validate_discount(code: str, user_id: int) -> dict:
    """
    بررسی و تایید کد تخفیف. خروجی: dict با کلیدهای valid, percent, reason
    """
    async with async_session() as session:
        res = await session.execute(select(DiscountCode).where(DiscountCode.code == code.upper()))
        dc = res.scalar_one_or_none()
        if not dc or not dc.is_active:
            return {"valid": False, "reason": "کد نامعتبر است."}
        if dc.expires_at and dc.expires_at < datetime.utcnow():
            return {"valid": False, "reason": "کد منقضی شده است."}
        if dc.max_uses > 0 and dc.used_count >= dc.max_uses:
            return {"valid": False, "reason": "ظرفیت استفاده از این کد به اتمام رسید."}

        u_res = await session.execute(select(User).where(User.telegram_id == user_id))
        user = u_res.scalar_one_or_none()
        if user:
            used_res = await session.execute(
                select(DiscountUsage).where(
                    DiscountUsage.code_id == dc.id,
                    DiscountUsage.user_id == user.id
                )
            )
            if used_res.scalar_one_or_none():
                return {"valid": False, "reason": "شما قبلا از این کد استفاده کرده‌اید."}

        return {"valid": True, "percent": dc.percent, "code_id": dc.id}