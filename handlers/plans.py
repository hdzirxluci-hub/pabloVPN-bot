from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import select

from database.db import async_session
from database.models import Plan, Panel
from utils.decorators import owner_only
from utils.keyboards import owner_main_kb, back_kb
from utils.states import OwnerStates
from utils.texts import t

router = Router()

@router.message(F.text == "📦 مدیریت پلن‌ها")
@owner_only
async def plans_menu(message: Message, state: FSMContext):
    async with async_session() as session:
        res = await session.execute(select(Plan))
        plans = res.scalars().all()

    plans_text = "\n".join([
        f"• {p.name} - {int(p.price):,} تومان - {p.traffic_gb}GB - {p.duration_days} روز"
        for p in plans
    ]) or "هیچ پلنی ثبت نشده."

    await message.answer(
        f"📦 <b>پلن‌های فعلی:</b>\n\n{plans_text}\n\nبرای افزودن پلن جدید، نام پلن را وارد کنید:",
        reply_markup=back_kb()
    )
    await state.set_state(OwnerStates.waiting_plan_name)

@router.message(OwnerStates.waiting_plan_name)
@owner_only
async def plan_name(message: Message, state: FSMContext):
    if message.text == t("back"):
        await state.clear()
        await message.answer("لغو شد.", reply_markup=owner_main_kb())
        return
    await state.update_data(plan_name=message.text.strip())

    async with async_session() as session:
        res = await session.execute(select(Panel).where(Panel.is_active == True))
        panels = res.scalars().all()

    if not panels:
        await state.clear()
        await message.answer("❌ ابتدا باید حداقل یک پنل متصل کنید.", reply_markup=owner_main_kb())
        return

    panels_text = "\n".join([f"ID {p.id}: {p.name}" for p in panels])
    await state.set_state(OwnerStates.waiting_plan_panel)
    await message.answer(f"پنل‌های موجود:\n{panels_text}\n\nآیدی پنل مربوطه را وارد کنید:")

@router.message(OwnerStates.waiting_plan_panel)
@owner_only
async def plan_panel(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ لطفا آیدی عددی پنل را وارد کنید.")
        return
    await state.update_data(plan_panel=int(message.text))
    await state.set_state(OwnerStates.waiting_plan_days)
    await message.answer("مدت زمان پلن به روز را وارد کنید (مثلا 30):")

@router.message(OwnerStates.waiting_plan_days)
@owner_only
async def plan_days(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ یک عدد صحیح وارد کنید.")
        return
    await state.update_data(plan_days=int(message.text))
    await state.set_state(OwnerStates.waiting_plan_gb)
    await message.answer("حجم پلن به گیگابایت (مثلا 30):")

@router.message(OwnerStates.waiting_plan_gb)
@owner_only
async def plan_gb(message: Message, state: FSMContext):
    try:
        gb = float(message.text)
    except ValueError:
        await message.answer("❌ عدد نامعتبر.")
        return
    await state.update_data(plan_gb=gb)
    await state.set_state(OwnerStates.waiting_plan_price)
    await message.answer("قیمت پلن به تومان (مثلا 100000):")

@router.message(OwnerStates.waiting_plan_price)
@owner_only
async def plan_price(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ عدد نامعتبر.")
        return
    data = await state.get_data()
    async with async_session() as session:
        plan = Plan(
            name=data["plan_name"],
            panel_id=data["plan_panel"],
            duration_days=data["plan_days"],
            traffic_gb=data["plan_gb"],
            price=float(message.text),
            is_active=True
        )
        session.add(plan)
        await session.commit()

    await state.clear()
    await message.answer("✅ پلن با موفقیت اضافه شد.", reply_markup=owner_main_kb())