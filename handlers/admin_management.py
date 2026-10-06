from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import select

from database.db import async_session
from database.models import User
from utils.decorators import owner_only
from utils.keyboards import owner_main_kb, back_kb
from utils.states import OwnerStates
from utils.texts import t

router = Router()

AVAILABLE_PERMISSIONS = ["receipts", "users", "tickets", "stats", "wallet_charge", "services"]

@router.message(F.text == "🛡️ مدیریت ادمین‌ها")
@owner_only
async def admin_management_menu(message: Message, state: FSMContext):
    async with async_session() as session:
        res = await session.execute(select(User).where(User.is_admin == True))
        admins = res.scalars().all()

    admins_text = "\n".join([
        f"👤 {a.first_name or '-'} | <code>{a.telegram_id}</code> | 🔑 {a.admin_permissions or 'all'}"
        for a in admins
    ]) or "هیچ ادمینی ثبت نشده."

    text = (
        f"🛡️ <b>مدیریت ادمین‌های ربات</b>\n\n"
        f"{admins_text}\n\n"
        f"برای افزودن ادمین جدید، آیدی عددی تلگرام او را بفرستید.\n"
        f"برای حذف، <code>del آیدی</code> را بفرستید (مثلا: <code>del 123456</code>)."
    )
    await state.set_state(OwnerStates.waiting_admin_id)
    await message.answer(text, reply_markup=back_kb())

@router.message(OwnerStates.waiting_admin_id)
@owner_only
async def admin_add_step(message: Message, state: FSMContext):
    if message.text == t("back"):
        await state.clear()
        await message.answer("لغو شد.", reply_markup=owner_main_kb())
        return

    text = message.text.strip()
    if text.lower().startswith("del "):
        try:
            tid = int(text.split(" ")[1])
        except Exception:
            await message.answer("❌ فرمت نادرست! مثال: <code>del 123456</code>")
            return
        async with async_session() as session:
            res = await session.execute(select(User).where(User.telegram_id == tid))
            u = res.scalar_one_or_none()
            if u:
                u.is_admin = False
                u.admin_permissions = ""
                await session.commit()
                await message.answer(f"✅ کاربر {tid} از لیست ادمین‌ها حذف شد.", reply_markup=owner_main_kb())
                await state.clear()
                return
            await message.answer("❌ کاربر یافت نشد.")
            return

    if not text.isdigit():
        await message.answer("❌ لطفا آیدی عددی ارسال کنید.")
        return

    await state.update_data(new_admin_id=int(text))
    await state.set_state(OwnerStates.waiting_admin_permissions)
    perms_list = ", ".join(AVAILABLE_PERMISSIONS)
    await message.answer(
        f"دسترسی‌های موجود:\n<code>{perms_list}</code>\n\n"
        f"برای ادمین کامل کلمه <code>all</code> را بفرستید، یا دسترسی‌ها را با کاما جدا کنید (مثلا: <code>receipts,tickets</code>):"
    )

@router.message(OwnerStates.waiting_admin_permissions)
@owner_only
async def admin_perms_step(message: Message, state: FSMContext):
    data = await state.get_data()
    tid = data["new_admin_id"]
    perms = message.text.strip().lower()

    if perms != "all":
        chosen = [p.strip() for p in perms.split(",")]
        valid = [p for p in chosen if p in AVAILABLE_PERMISSIONS]
        if not valid:
            await message.answer("❌ هیچ دسترسی معتبری انتخاب نشد.")
            return
        perms = ",".join(valid)

    async with async_session() as session:
        res = await session.execute(select(User).where(User.telegram_id == tid))
        u = res.scalar_one_or_none()
        if not u:
            u = User(telegram_id=tid, is_admin=True, admin_permissions=perms)
            session.add(u)
        else:
            u.is_admin = True
            u.admin_permissions = perms
        await session.commit()

    await state.clear()
    await message.answer(f"✅ کاربر {tid} با دسترسی <b>{perms}</b> به عنوان ادمین اضافه شد.", reply_markup=owner_main_kb())