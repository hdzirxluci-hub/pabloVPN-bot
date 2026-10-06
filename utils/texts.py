from sqlalchemy import select
from database.db import async_session
from database.models import Setting

_cache = {}

async def get_setting(key: str, default: str = "") -> str:
    if key in _cache:
        return _cache[key]
    async with async_session() as session:
        result = await session.execute(select(Setting).where(Setting.key == key))
        setting = result.scalar_one_or_none()
        value = setting.value if setting else default
        _cache[key] = value
        return value

async def set_setting(key: str, value: str):
    async with async_session() as session:
        result = await session.execute(select(Setting).where(Setting.key == key))
        setting = result.scalar_one_or_none()
        if setting:
            setting.value = value
        else:
            session.add(Setting(key=key, value=value))
        await session.commit()
        _cache[key] = value

def clear_cache():
    _cache.clear()

async def get_brand() -> str:
    return await get_setting("brand_name", "PabloVPN")

async def format_text(key: str, default: str = "", **kwargs) -> str:
    text = await get_setting(key, default)
    brand = await get_brand()
    kwargs.setdefault("brand", brand)
    try:
        return text.format(**kwargs)
    except (KeyError, IndexError):
        return text

TEXTS = {
    "welcome_back": "👋 خوش آمدید!",
    "main_menu": "🏠 منوی اصلی",
    "user_menu_buy": "🛒 خرید سرویس",
    "user_menu_services": "📦 سرویس‌های من",
    "user_menu_wallet": "👛 کیف پول",
    "user_menu_test": "🎁 تست رایگان",
    "user_menu_referral": "👥 زیرمجموعه‌گیری",
    "user_menu_support": "💬 پشتیبانی",
    "user_menu_guide": "📚 راهنمای اتصال",
    "user_menu_about": "ℹ️ درباره ما",
    "user_menu_rules": "📜 قوانین",
    "owner_menu": "👑 پنل مالک",
    "admin_menu": "🛡️ پنل ادمین",
    "back": "🔙 بازگشت",
    "cancel": "❌ انصراف",
    "confirm": "✅ تایید",
    "yes": "✅ بله",
    "no": "❌ خیر",
    "operation_cancelled": "❌ عملیات لغو شد.",
    "operation_success": "✅ عملیات با موفقیت انجام شد.",
    "error_occurred": "❌ خطایی رخ داد. لطفا دوباره تلاش کنید.",
    "unauthorized": "⛔ شما دسترسی به این بخش ندارید.",
    "banned": "🚫 شما از ربات مسدود شده‌اید.",
    "join_required": "📢 برای استفاده از ربات باید در کانال‌های زیر عضو شوید:",
    "joined_check": "✅ عضو شدم",
    "not_joined": "❌ شما هنوز در همه کانال‌ها عضو نشده‌اید.",
    "insufficient_balance": "💸 موجودی کیف پول شما کافی نیست.\n\n💰 موجودی فعلی: {balance:,} تومان\n💵 مبلغ لازم: {needed:,} تومان",
    "charge_wallet": "💳 شارژ کیف پول",
    "wallet_balance": "👛 موجودی کیف پول شما: {balance:,} تومان",
    "enter_amount": "💵 لطفا مبلغ مورد نظر را به تومان وارد کنید:",
    "invalid_amount": "❌ مبلغ وارد شده نامعتبر است. لطفا یک عدد صحیح وارد کنید.",
    "amount_too_low": "❌ حداقل مبلغ شارژ {min:,} تومان است.",
    "amount_too_high": "❌ حداکثر مبلغ شارژ {max:,} تومان است.",
    "card_payment_info": "💳 لطفا مبلغ {amount:,} تومان را به کارت زیر واریز کنید:\n\n🏦 شماره کارت:\n<code>{card}</code>\n\n👤 به نام: {holder}\n\n📸 سپس عکس رسید را ارسال کنید.",
    "receipt_received": "✅ رسید شما دریافت شد و در حال بررسی است.\nپس از تایید، موجودی کیف پول شما شارژ خواهد شد.",
    "payment_approved": "✅ پرداخت شما تایید شد!\n💰 مبلغ {amount:,} تومان به کیف پول شما اضافه شد.",
    "payment_rejected": "❌ متاسفانه پرداخت شما تایید نشد.\n📝 دلیل: {reason}",
    "ticket_create": "📝 ایجاد تیکت جدید",
    "ticket_subject": "📋 لطفا موضوع تیکت را وارد کنید:",
    "ticket_message": "✍️ لطفا پیام خود را ارسال کنید (متن، عکس یا فایل):",
    "ticket_created": "✅ تیکت شما با شماره #{id} ایجاد شد.\nپاسخ در این‌جا به شما ارسال خواهد شد.",
    "ticket_reply": "💬 پاسخ ادمین به تیکت #{id}:\n\n{text}",
    "ticket_closed": "🔒 تیکت #{id} بسته شد.",
    "my_tickets": "📋 تیکت‌های من",
    "no_tickets": "📭 شما تیکتی ندارید.",
    "referral_info": "👥 سیستم زیرمجموعه‌گیری\n\n🔗 لینک دعوت شما:\n{link}\n\n👤 تعداد زیرمجموعه‌ها: {count}\n💰 درآمد شما: {earnings:,} تومان\n\n💡 با هر خرید زیرمجموعه‌تان، {percent}% به شما تعلق می‌گیرد.",
    "no_services": "📭 شما سرویس فعالی ندارید.",
    "service_info": "📦 اطلاعات سرویس\n\n🏷️ نام: {name}\n📊 حجم: {traffic} GB\n⏱️ مدت: {days} روز\n📅 انقضا: {expires}\n\n🔗 لینک اتصال:\n<code>{link}</code>",
    "free_trial_used": "⚠️ شما قبلا از تست رایگان استفاده کرده‌اید.",
    "free_trial_disabled": "⚠️ تست رایگان در حال حاضر غیرفعال است.",
    "free_trial_success": "🎁 سرویس تست رایگان شما ساخته شد!",
}

def t(key: str, **kwargs) -> str:
    text = TEXTS.get(key, key)
    try:
        return text.format(**kwargs)
    except (KeyError, IndexError):
        return text