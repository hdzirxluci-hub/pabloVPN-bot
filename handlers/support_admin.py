from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select, func

from database.db import async_session
from database.models import Ticket, TicketMessage, User
from utils.decorators import admin_only, owner_only
from utils.keyboards import owner_main_kb, back_kb
from utils.texts import t

router = Router()


class SupportStates(StatesGroup):
    waiting_ticket_id = State()
    waiting_reply = State()


@router.message(F.text == "💬 مدیریت پشتیبانی")
@owner_only
async def support_mgmt_menu(message: Message, state: FSMContext):
    async with async_session() as session:
        open_count = await session.scalar(
            select(func.count(Ticket.id)).where(Ticket.status == "open")
        ) or 0
        closed_count = await session.scalar(
            select(func.count(Ticket.id)).where(Ticket.status == "closed")
        ) or 0
        
        open_tickets_res = await session.execute(
            select(Ticket).where(Ticket.status == "open").order_by(Ticket.id.desc()).limit(10)
        )
        open_tickets = open_tickets_res.scalars().all()
    
    text = (
        f"💬 <b>مدیریت تیکت‌های پشتیبانی</b>\n\n"
        f"📬 تیکت‌های باز: {open_count}\n"
        f"🔒 تیکت‌های بسته: {closed_count}\n\n"
    )
    
    if open_tickets:
        text += "<b>📋 ۱۰ تیکت باز اخیر:</b>\n"
        for tk in open_tickets:
            text += f"• #{tk.id} - {tk.created_at.strftime('%m/%d %H:%M')}\n"
        text += f"\n💡 برای مشاهده و پاسخ به تیکت، شماره آن را بفرستید (مثلا <code>5</code>):"
    else:
        text += "📭 هیچ تیکت بازی وجود ندارد."
    
    await state.set_state(SupportStates.waiting_ticket_id)
    await message.answer(text, reply_markup=back_kb())


@router.message(SupportStates.waiting_ticket_id)
@owner_only
async def view_ticket(message: Message, state: FSMContext):
    if message.text == t("back"):
        await state.clear()
        await message.answer("لغو شد.", reply_markup=owner_main_kb())
        return
    
    if not message.text.strip().isdigit():
        await message.answer("❌ لطفا شماره تیکت را عدد وارد کنید.")
        return
    
    ticket_id = int(message.text.strip())
    async with async_session() as session:
        tk_res = await session.execute(select(Ticket).where(Ticket.id == ticket_id))
        ticket = tk_res.scalar_one_or_none()
        
        if not ticket:
            await message.answer("❌ تیکت یافت نشد.")
            return
        
        user_res = await session.execute(select(User).where(User.id == ticket.user_id))
        user = user_res.scalar_one_or_none()
        
        msgs_res = await session.execute(
            select(TicketMessage).where(TicketMessage.ticket_id == ticket.id).order_by(TicketMessage.id)
        )
        msgs = msgs_res.scalars().all()
    
    text = f"🎫 <b>تیکت #{ticket.id}</b>\n"
    text += f"👤 کاربر: <code>{user.telegram_id if user else '-'}</code>\n"
    text += f"📅 تاریخ: {ticket.created_at.strftime('%Y/%m/%d %H:%M')}\n"
    text += f"📌 وضعیت: {ticket.status}\n\n"
    text += "<b>💬 مکالمات:</b>\n\n"
    
    for m in msgs:
        sender = "👨‍💼 ادمین" if m.is_admin else "👤 کاربر"
        text += f"{sender}:\n{m.message_text or '(فایل)'}\n\n"
    
    text += (
        f"<b>⚙️ عملیات:</b>\n"
        f"• برای پاسخ، کلمه <code>reply</code> را بفرستید\n"
        f"• برای بستن تیکت، کلمه <code>close</code> را بفرستید\n"
        f"• برای تیکت دیگر، شماره جدید را بفرستید"
    )
    
    await state.update_data(current_ticket=ticket.id, target_user_tg=user.telegram_id if user else None)
    await message.answer(text)


@router.message(F.text.in_(["reply", "close"]), SupportStates.waiting_ticket_id)
@owner_only
async def ticket_action(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    ticket_id = data.get("current_ticket")
    
    if not ticket_id:
        await message.answer("❌ ابتدا یک تیکت انتخاب کنید.")
        return
    
    if message.text == "close":
        from datetime import datetime
        async with async_session() as session:
            tk = await session.get(Ticket, ticket_id)
            if tk:
                tk.status = "closed"
                tk.closed_at = datetime.utcnow()
                await session.commit()
        
        target_tg = data.get("target_user_tg")
        if target_tg:
            try:
                await bot.send_message(target_tg, t("ticket_closed", id=ticket_id))
            except Exception:
                pass
        
        await state.clear()
        await message.answer(f"✅ تیکت #{ticket_id} بسته شد.", reply_markup=owner_main_kb())
        return
    
    if message.text == "reply":
        await state.set_state(SupportStates.waiting_reply)
        await message.answer("✍️ متن پاسخ خود را ارسال کنید:", reply_markup=back_kb())


@router.message(SupportStates.waiting_reply)
@owner_only
async def send_reply(message: Message, state: FSMContext, bot: Bot):
    if message.text == t("back"):
        await state.clear()
        await message.answer("لغو شد.", reply_markup=owner_main_kb())
        return
    
    data = await state.get_data()
    ticket_id = data.get("current_ticket")
    target_tg = data.get("target_user_tg")
    
    async with async_session() as session:
        tk = await session.get(Ticket, ticket_id)
        if not tk:
            await message.answer("❌ تیکت یافت نشد.")
            await state.clear()
            return
        
        reply_msg = TicketMessage(
            ticket_id=ticket_id,
            sender_id=message.from_user.id,
            is_admin=True,
            message_text=message.text
        )
        session.add(reply_msg)
        tk.status = "in_progress"
        await session.commit()
    
    if target_tg:
        try:
            await bot.send_message(
                target_tg,
                t("ticket_reply", id=ticket_id, text=message.text)
            )
        except Exception:
            pass
    
    await state.clear()
    await message.answer(f"✅ پاسخ ارسال شد.", reply_markup=owner_main_kb())