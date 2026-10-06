from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import select

from database.db import async_session
from database.models import Ticket, TicketMessage, User
from utils.keyboards import back_kb, main_menu_kb
from utils.states import TicketStates
from utils.texts import get_setting, t

router = Router()

@router.message(F.text == t("user_menu_support"))
async def support_menu(message: Message, state: FSMContext):
    await state.set_state(TicketStates.waiting_message)
    await message.answer(
        "💬 <b>ارسال پیام به پشتیبانی</b>\n\nلطفا پیام یا سوال خود را به صورت کامل ارسال نمایید:",
        reply_markup=back_kb()
    )

@router.message(TicketStates.waiting_message)
async def submit_ticket(message: Message, state: FSMContext, bot: Bot):
    if message.text == t("back"):
        await state.clear()
        await message.answer("لغو شد.", reply_markup=main_menu_kb())
        return

    async with async_session() as session:
        u_res = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
        user = u_res.scalar_one_or_none()
        if not user:
            return

        ticket = Ticket(user_id=user.id, subject="پشتیبانی مستقیم", status="open")
        session.add(ticket)
        await session.flush()

        msg_body = message.text or message.caption or "فایل ضمیمه شده"
        t_msg = TicketMessage(
            ticket_id=ticket.id,
            sender_id=message.from_user.id,
            is_admin=False,
            message_text=msg_body
        )
        session.add(t_msg)
        await session.commit()
        ticket_id = ticket.id

    support_group = await get_setting("support_group_id", "")
    if support_group:
        alert = (
            f"📬 <b>تیکت جدید #{ticket_id}</b>\n\n"
            f"👤 کاربر: <code>{message.from_user.id}</code> (@{message.from_user.username or 'ندارد'})\n"
            f"💬 پیام: {msg_body}"
        )
        try:
            await bot.send_message(chat_id=support_group, text=alert)
        except Exception:
            pass

    await state.clear()
    await message.answer(t("ticket_created", id=ticket_id), reply_markup=main_menu_kb())