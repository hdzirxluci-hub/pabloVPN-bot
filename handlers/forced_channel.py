from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import select

from database.db import async_session
from database.models import ForcedChannel, Setting
from utils.decorators import owner_only
from utils.keyboards import owner_main_kb, back_kb
from utils.states import OwnerStates
from utils.texts import set_setting, get_setting, t

router = Router()

@router.message(F.text == "🔒 عضویت اجباری")
@owner_only
async def forced_menu(message: Message, state: FSMContext):
    enabled = await get_setting("channel_lock_enabled", "0")
    status = "🟢 فعال" if enabled == "1" else "🔴 غیرفعال"

    async with async_session() as session:
        res = await session.execute(select(ForcedChannel).where(ForcedChannel.is_active == True))
        channels = res.scalars().all()

    channels_text = "\n".join([f"• {c.channel_title or c.channel_id}" for c in channels]) or "هیچ کانالی ثبت نشده"

    text = (
        f"🔒 <b>تنظیمات عضویت اجباری</b>\n\n"
        f"وضعیت: {status}\n\n"
        f"کانال‌های فعلی:\n{channels_text}\n\n"
        f"برای فعال/غیرفعال کردن کلمه <code>toggle</code> را بفرستید.\n"
        f"برای افزودن کانال، آیدی عددی یا یوزرنیم کانال (مثل @mychannel) را بفرستید.\n"
        f"⚠️ ربات باید در کانال ادمین باشد."
    )
    await state.set_state(OwnerStates.waiting_forced_channel)
    await message.answer(text, reply_markup=back_kb())

@router.message(OwnerStates.waiting_forced_channel)
@owner_only
async def forced_add(message: Message, state: FSMContext, bot: Bot):
    if message.text == t("back"):
        await state.clear()
        await message.answer("لغو شد.", reply_markup=owner_main_kb())
        return

    text = message.text.strip()
    if text.lower() == "toggle":
        current = await get_setting("channel_lock_enabled", "0")
        new = "0" if current == "1" else "1"
        await set_setting("channel_lock_enabled", new)
        status = "🟢 فعال" if new == "1" else "🔴 غیرفعال"
        await state.clear()
        await message.answer(f"✅ عضویت اجباری اکنون {status} است.", reply_markup=owner_main_kb())
        return

    try:
        chat = await bot.get_chat(text)
        channel_id = str(chat.id)
        username = chat.username
        title = chat.title
        invite = None
        try:
            invite = await bot.export_chat_invite_link(chat.id)
        except Exception:
            pass

        async with async_session() as session:
            fc = ForcedChannel(
                channel_id=channel_id,
                channel_username=username,
                channel_title=title,
                invite_link=invite,
                is_active=True
            )
            session.add(fc)
            await session.commit()

        await state.clear()
        await message.answer(f"✅ کانال «{title}» اضافه شد.", reply_markup=owner_main_kb())
    except Exception as e:
        await message.answer(f"❌ خطا در افزودن کانال: مطمئن شوید ربات ادمین است.\n{e}")