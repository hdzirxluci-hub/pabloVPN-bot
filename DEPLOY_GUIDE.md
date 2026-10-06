# 🚀 راهنمای کامل راه‌اندازی PabloVPN-Bot

## 📱 گام ۱: ساخت ریپازیتوری در GitHub از گوشی

1. وارد اپ GitHub شو یا به [github.com](https://github.com) برو
2. دکمه ➕ بالا راست → **New repository**
3. نام: `PabloVPN-Bot`
4. Public (برای عمومی بودن) انتخاب کن
5. تیک **Add a README file** رو بزن
6. دکمه **Create repository** بزن

---

## 📂 گام ۲: آپلود فایل‌ها در GitHub

### روش ساده (از مرورگر گوشی):
1. وارد ریپو شو
2. دکمه **Add file** → **Create new file**
3. نام فایل رو با مسیر وارد کن (مثلا: `database/db.py`)
4. محتوای کد رو paste کن
5. پایین صفحه → **Commit changes**
6. این کار رو برای همه ۵۰ فایل انجام بده

> 💡 **نکته:** برای ساخت پوشه، کافیه در نام فایل `/` بذاری. مثلا `handlers/user.py` خودش پوشه handlers رو می‌سازه.

### لیست کامل فایل‌ها:
ببین ما قراره ی کار خیلی خفن بکنیم پس حواستو خوب جمع کن ما قراره روی ریلوی یدونه ربات فروش vpn راه ا

Max


بسم‌الله! بریم برای بسته آخر 🔥

📦 بسته سوم: ۱۰ فایل نهایی (پرداخت‌های تکمیلی + تنظیمات نهایی + فایل‌های دیپلوی)
4️⃣1️⃣ payments/crypto.py
Python

import aiohttp
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

class CryptoPayment:
    """
    پرداخت رمزارز با استفاده از NowPayments API
    برای فعالسازی، API Key رو از nowpayments.io بگیرید و در تنظیمات ربات ذخیره کنید.
    """

    BASE_URL = "https://api.nowpayments.io/v1"

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def create_invoice(self, amount_usd: float, order_id: str, description: str = "") -> Optional[Dict]:
        if not self.api_key:
            logger.warning("NowPayments API key not set")
            return None

        headers = {"x-api-key": self.api_key, "Content-Type": "application/json"}
        payload = {
            "price_amount": amount_usd,
            "price_currency": "usd",
            "order_id": order_id,
            "order_description": description or f"Order #{order_id}",
            "ipn_callback_url": "",
            "success_url": "",
            "cancel_url": ""
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.BASE_URL}/invoice", json=payload, headers=headers, timeout=15) as resp:
                    if resp.status in [200, 201]:
                        data = await resp.json()
                        return {
                            "invoice_url": data.get("invoice_url"),
                            "invoice_id": data.get("id"),
                            "status": data.get("status", "waiting")
                        }
                    else:
                        text = await resp.text()
                        logger.error(f"NowPayments error {resp.status}: {text}")
        except Exception as e:
            logger.error(f"Crypto invoice error: {e}")
        return None

    async def get_payment_status(self, invoice_id: str) -> Optional[str]:
        if not self.api_key:
            return None
        headers = {"x-api-key": self.api_key}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.BASE_URL}/payment/{invoice_id}", headers=headers, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("payment_status")
        except Exception as e:
            logger.error(f"Crypto status check error: {e}")
        return None

    @staticmethod
    def toman_to_usd(amount_toman: float, usd_rate: float = 60000) -> float:
        """
        تبدیل تومان به دلار بر اساس نرخ تنظیم‌شده توسط مالک.
        """
        if usd_rate <= 0:
            usd_rate = 60000
        return round(amount_toman / usd_rate, 2)
4️⃣2️⃣ payments/zarinpal.py
Python

import aiohttp
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

class ZarinpalPayment:
    """
    پرداخت از طریق درگاه ریالی زرین‌پال.
    MerchantID رو از zarinpal.com بگیرید و در تنظیمات ربات ذخیره کنید.
    """

    REQUEST_URL = "https://api.zarinpal.com/pg/v4/payment/request.json"
    VERIFY_URL = "https://api.zarinpal.com/pg/v4/payment/verify.json"
    GATEWAY_URL = "https://www.zarinpal.com/pg/StartPay/"

    def __init__(self, merchant_id: str, callback_url: str = ""):
        self.merchant_id = merchant_id
        self.callback_url = callback_url or "https://example.com/callback"

    async def create_payment(self, amount_toman: int, description: str = "", mobile: str = "", email: str = "") -> Optional[Dict]:
        if not self.merchant_id:
            logger.warning("Zarinpal MerchantID not set")
            return None

        payload = {
            "merchant_id": self.merchant_id,
            "amount": amount_toman * 10,  # تبدیل تومان به ریال
            "description": description or "شارژ کیف پول",
            "callback_url": self.callback_url,
            "metadata": {"mobile": mobile, "email": email}
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.REQUEST_URL, json=payload, timeout=15) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        d = data.get("data", {})
                        if d.get("code") == 100:
                            authority = d.get("authority")
                            return {
                                "authority": authority,
                                "gateway_url": f"{self.GATEWAY_URL}{authority}"
                            }
                        else:
                            logger.error(f"Zarinpal error: {data.get('errors')}")
        except Exception as e:
            logger.error(f"Zarinpal request error: {e}")
        return None

    async def verify_payment(self, authority: str, amount_toman: int) -> Optional[Dict]:
        if not self.merchant_id:
            return None
        payload = {
            "merchant_id": self.merchant_id,
            "amount": amount_toman * 10,
            "authority": authority
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.VERIFY_URL, json=payload, timeout=15) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        d = data.get("data", {})
                        if d.get("code") in [100, 101]:
                            return {
                                "success": True,
                                "ref_id": d.get("ref_id"),
                                "card_pan": d.get("card_pan")
                            }
        except Exception as e:
            logger.error(f"Zarinpal verify error: {e}")
        return {"success": False}
4️⃣3️⃣ handlers/discount.py
Python

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
4️⃣4️⃣ handlers/trial.py
Python

from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy import select

from database.db import async_session
from database.models import Panel, Service, User
from panels import get_panel_adapter
from utils.texts import get_setting, format_date, t

router = Router()

@router.message(F.text == t("user_menu_test"))
async def give_trial(message: Message):
    enabled = await get_setting("free_trial_enabled", "0")
    if enabled != "1":
        await message.answer(t("free_trial_disabled"))
        return

    async with async_session() as session:
        u_res = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
        user = u_res.scalar_one_or_none()
        if not user:
            return

        if user.free_trial_used:
            await message.answer(t("free_trial_used"))
            return

        p_res = await session.execute(select(Panel).where(Panel.is_active == True).limit(1))
        panel = p_res.scalar_one_or_none()

    if not panel:
        await message.answer("⚠️ در حال حاضر امکان ارائه سرویس تست وجود ندارد.")
        return

    days = int(await get_setting("free_trial_days", "1"))
    gb = float(await get_setting("free_trial_gb", "1"))

    adapter = get_panel_adapter(panel)
    username = f"trial_{message.from_user.id}_{int(datetime.utcnow().timestamp())}"
    await message.answer("⏳ در حال ساخت سرویس تست رایگان...")

    success, sub_link, config_data = await adapter.create_user(username=username, traffic_gb=gb, duration_days=days)

    if not success:
        await message.answer("❌ خطا در ساخت سرویس تست. لطفا با پشتیبانی تماس بگیرید.")
        return

    expires = datetime.utcnow() + timedelta(days=days)
    async with async_session() as session:
        u = await session.get(User, user.id)
        u.free_trial_used = True
        srv = Service(
            user_id=u.id,
            panel_id=panel.id,
            username=username,
            subscription_url=sub_link,
            config_data=config_data,
            traffic_gb=gb,
            duration_days=days,
            expires_at=expires,
            is_trial=True
        )
        session.add(srv)
        await session.commit()

    text = (
        f"🎁 <b>{t('free_trial_success')}</b>\n\n"
        f"📊 حجم: {gb} GB\n"
        f"⏱️ مدت: {days} روز\n"
        f"📅 انقضا: {format_date(expires)}\n\n"
        f"🔗 لینک اتصال:\n<code>{sub_link or config_data}</code>"
    )
    await message.answer(text)
4️⃣5️⃣ handlers/forced_channel.py
Python

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
4️⃣6️⃣ handlers/admin_management.py
Python

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
4️⃣7️⃣ handlers/plans.py
Python

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
4️⃣8️⃣ handlers/__init__.py (آپدیت نهایی)
Python

from . import (
    start,
    user,
    owner,
    admin,
    wallet,
    payment,
    purchase,
    support,
    referral,
    backup,
    discount,
    trial,
    forced_channel,
    admin_management,
    plans,
)
نکته: این فایل جایگزین نسخه قبلی در بسته دوم می‌شود.

4️⃣9️⃣ main.py (نسخه نهایی - جایگزین نسخه قبلی)
Python

import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import config
from database.db import init_db
from handlers import (
    start, user, owner, admin, wallet, payment,
    purchase, support, referral, backup,
    discount, trial, forced_channel, admin_management, plans
)
from middlewares.throttling import ThrottlingMiddleware
from middlewares.auth import AuthMiddleware
from utils.scheduler import setup_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

async def on_startup(bot: Bot):
    logger.info("🚀 PabloVPN-Bot در حال راه‌اندازی...")
    await init_db()
    logger.info("✅ دیتابیس آماده شد")
    try:
        await bot.send_message(
            config.OWNER_ID,
            "✅ <b>PabloVPN-Bot فعال شد!</b>\n\n🎉 خوش آمدید مالک گرامی.\n\nبرای ورود به پنل مدیریت از دکمه <b>👑 پنل مالک</b> در منوی اصلی استفاده کنید."
        )
    except Exception as e:
        logger.warning(f"نتوانست به مالک پیام بفرستد: {e}")

async def on_shutdown(bot: Bot):
    logger.info("🛑 ربات در حال خاموش شدن...")

async def main():
    try:
        config.validate()
    except ValueError as e:
        logger.error(f"خطا در تنظیمات: {e}")
        return

    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Middlewares
    dp.message.middleware(ThrottlingMiddleware())
    dp.callback_query.middleware(ThrottlingMiddleware())
    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())

    # Routers (ترتیب مهم است - owner و admin اول باشند)
    dp.include_router(start.router)
    dp.include_router(owner.router)
    dp.include_router(admin.router)
    dp.include_router(admin_management.router)
    dp.include_router(forced_channel.router)
    dp.include_router(plans.router)
    dp.include_router(discount.router)
    dp.include_router(backup.router)
    dp.include_router(trial.router)
    dp.include_router(wallet.router)
    dp.include_router(payment.router)
    dp.include_router(purchase.router)
    dp.include_router(support.router)
    dp.include_router(referral.router)
    dp.include_router(user.router)  # این باید آخر باشد (برای catch all)

    # Scheduler
    scheduler = AsyncIOScheduler(timezone=config.TIMEZONE)
    setup_scheduler(scheduler, bot)
    scheduler.start()

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("🤖 PabloVPN-Bot فعال شد!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("👋 خداحافظ!")
نکته: این فایل جایگزین main.py بسته اول می‌شود.

5️⃣0️⃣ DEPLOY_GUIDE.md (راهنمای کامل دیپلوی)
Markdown

# 🚀 راهنمای کامل راه‌اندازی PabloVPN-Bot

## 📱 گام ۱: ساخت ریپازیتوری در GitHub از گوشی

1. وارد اپ GitHub شو یا به [github.com](https://github.com) برو
2. دکمه ➕ بالا راست → **New repository**
3. نام: `PabloVPN-Bot`
4. Public (برای عمومی بودن) انتخاب کن
5. تیک **Add a README file** رو بزن
6. دکمه **Create repository** بزن

---

## 📂 گام ۲: آپلود فایل‌ها در GitHub

### روش ساده (از مرورگر گوشی):
1. وارد ریپو شو
2. دکمه **Add file** → **Create new file**
3. نام فایل رو با مسیر وارد کن (مثلا: `database/db.py`)
4. محتوای کد رو paste کن
5. پایین صفحه → **Commit changes**
6. این کار رو برای همه ۵۰ فایل انجام بده

> 💡 **نکته:** برای ساخت پوشه، کافیه در نام فایل `/` بذاری. مثلا `handlers/user.py` خودش پوشه handlers رو می‌سازه.

### لیست کامل فایل‌ها:
PabloVPN-Bot/
├── README.md
├── requirements.txt
├── Procfile
├── railway.json
├── .gitignore
├── .env.example
├── config.py
├── main.py
├── database/
│ ├── init.py
│ ├── db.py
│ └── models.py
├── handlers/
│ ├── init.py
│ ├── start.py
│ ├── user.py
│ ├── owner.py
│ ├── admin.py
│ ├── admin_management.py
│ ├── wallet.py
│ ├── payment.py
│ ├── purchase.py
│ ├── support.py
│ ├── referral.py
│ ├── backup.py
│ ├── discount.py
│ ├── trial.py
│ ├── forced_channel.py
│ └── plans.py
├── panels/
│ ├── init.py
│ ├── base.py
│ ├── marzban.py
│ ├── three_xui.py
│ ├── sanaei.py
│ └── pasargad.py
├── payments/
│ ├── init.py
│ ├── card.py
│ ├── crypto.py
│ └── zarinpal.py
├── utils/
│ ├── init.py
│ ├── texts.py
│ ├── keyboards.py
│ ├── helpers.py
│ ├── decorators.py
│ ├── states.py
│ └── scheduler.py
└── middlewares/
├── init.py
├── auth.py
└── throttling.py

> ⚠️ فایل‌های خالی `__init__.py` حتما باید ساخته بشن (محتوا رو خالی بذار یا کامنت کوتاه).

---

## 🚂 گام ۳: دیپلوی روی Railway

1. وارد [railway.app](https://railway.app) شو
2. **Login with GitHub**
3. دکمه **New Project** 
4. **Deploy from GitHub repo** رو انتخاب کن
5. ریپو `PabloVPN-Bot` رو انتخاب کن
6. منتظر بمون تا پروژه ساخته شه

---

## 🔑 گام ۴: تنظیم متغیرهای محیطی

1. در Railway وارد پروژه‌ت شو
2. تب **Variables** رو باز کن
3. دکمه **New Variable** و این‌ها رو اضافه کن:

| نام | مقدار |
|-----|-------|
| `BOT_TOKEN` | توکن ربات از BotFather |
| `OWNER_ID` | آیدی عددی تلگرام تو |
| `TIMEZONE` | `Asia/Tehran` |

4. دکمه **Deploy** → ربات بالا میاد ✅

---

## ✅ گام ۵: تست و راه‌اندازی

1. وارد ربات تلگرامت شو
2. دستور `/start` بزن
3. اگر پیام خوش‌آمد اومد → ✅ موفقیت
4. دکمه **👑 پنل مالک** → ورود به تنظیمات

---

## ⚙️ گام ۶: تنظیمات اولیه در ربات

### ۱. تنظیم کارت بانکی:
`پنل مالک` → `💳 تنظیمات پرداخت` → وارد کردن شماره کارت و نام صاحب

### ۲. اتصال پنل VPN:
`پنل مالک` → `🔌 مدیریت پنل‌ها` → وارد کردن مشخصات پنل

### ۳. ساخت پلن فروش:
`پنل مالک` → `📦 مدیریت پلن‌ها` → تعریف پلن‌ها

### ۴. تنظیم کانال رسید (اختیاری):
یه کانال خصوصی بساز → ربات رو ادمین کن → آیدی کانال رو در تنظیمات ذخیره کن

### ۵. تنظیم عضویت اجباری (اختیاری):
`پنل مالک` → `🔒 عضویت اجباری` → `toggle` → افزودن کانال

---

## 💾 گام ۷: بکاپ و مهاجرت (مهم!)

### دریافت بکاپ:
`پنل مالک` → `💾 بکاپ و ریستور` → `/get_backup`
فایل `.db` رو ذخیره کن (توی چت ذخیره شده).

### مهاجرت به اکانت جدید Railway (روز ۲۹):
1. با ایمیل جدید در Railway ثبت‌نام کن
2. همون ریپو GitHub رو دیپلوی کن
3. متغیرهای `BOT_TOKEN` و `OWNER_ID` رو ست کن
4. وارد ربات شو → `پنل مالک` → `💾 بکاپ و ریستور` → `/restore`
5. فایل `.db` قدیمی رو بفرست → همه چی برمی‌گرده ✅

---

## 🎨 شخصی‌سازی برندینگ

### تغییر نام برند:
`پنل مالک` → `🎨 برندینگ و متن‌ها` → وارد کردن نام جدید (مثلا `MyVPN`)

تمام متن‌های ربات به صورت خودکار از این نام استفاده می‌کنن.

---

## ⚠️ عیب‌یابی

### ربات پیام نمی‌ده:
- چک کن `BOT_TOKEN` درست باشه
- در Railway → تب **Deployments** → **View Logs** چک کن

### دکمه پنل مالک نیست:
- `OWNER_ID` رو درست وارد کردی؟ (آیدی عددی، نه یوزرنیم)
- `/start` بزن مجدد

### پنل VPN وصل نمی‌شه:
- آدرس URL با پورت و `https://` باشه
- یوزرنیم و پسورد پنل درست باشن
- پنل در دسترس باشه

### خطای Deploy در Railway:
- فایل `requirements.txt` کامل باشه
- فایل `Procfile` موجود باشه
- دوباره **Redeploy** بزن

---

## 📞 پشتیبانی و مشارکت

برای گزارش باگ یا پیشنهاد، در ریپو **Issue** باز کن.

---

# 🎉 موفق باشی! PabloVPN آماده‌ست! 🚀