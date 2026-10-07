from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from utils.texts import t

def main_menu_kb(is_owner: bool = False, is_admin: bool = False, show_trial: bool = False) -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text=t("user_menu_buy")), KeyboardButton(text=t("user_menu_services"))],
        [KeyboardButton(text=t("user_menu_wallet")), KeyboardButton(text=t("user_menu_referral"))],
    ]
    if show_trial:
        buttons.append([KeyboardButton(text=t("user_menu_test"))])
    buttons.append([KeyboardButton(text=t("user_menu_support")), KeyboardButton(text=t("user_menu_guide"))])
    buttons.append([KeyboardButton(text=t("user_menu_about")), KeyboardButton(text=t("user_menu_rules"))])
    if is_owner:
        buttons.append([KeyboardButton(text=t("owner_menu"))])
    elif is_admin:
        buttons.append([KeyboardButton(text=t("admin_menu"))])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def back_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t("back"))]],
        resize_keyboard=True
    )

def cancel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t("cancel"))]],
        resize_keyboard=True
    )

def confirm_inline_kb(yes_data: str, no_data: str = "cancel") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=t("yes"), callback_data=yes_data),
            InlineKeyboardButton(text=t("no"), callback_data=no_data),
        ]
    ])

def owner_main_kb() -> ReplyKeyboardMarkup:
    """منوی اصلی مالک - کامل و دسته‌بندی شده"""
    buttons = [
        # ردیف ۱: آمار و مدیریت کاربران
        [KeyboardButton(text="📊 آمار ربات"), KeyboardButton(text="👥 مدیریت کاربران")],
        # ردیف ۲: ادمین‌ها و پنل‌ها
        [KeyboardButton(text="🛡️ مدیریت ادمین‌ها"), KeyboardButton(text="🔌 مدیریت پنل‌ها")],
        # ردیف ۳: پلن‌ها و تخفیف
        [KeyboardButton(text="📦 مدیریت پلن‌ها"), KeyboardButton(text="🎁 زیرمجموعه و تخفیف")],
        # ردیف ۴: پرداخت
        [KeyboardButton(text="💳 تنظیمات پرداخت"), KeyboardButton(text="💵 روش‌های پرداخت")],
        [KeyboardButton(text="💰 حداقل/حداکثر شارژ"), KeyboardButton(text="💹 درصد زیرمجموعه")],
        # ردیف ۵: کانال‌ها
        [KeyboardButton(text="📢 کانال رسید"), KeyboardButton(text="💬 گروه پشتیبانی")],
        [KeyboardButton(text="🔒 عضویت اجباری"), KeyboardButton(text="💬 مدیریت پشتیبانی")],
        # ردیف ۶: برندینگ
        [KeyboardButton(text="🎨 برندینگ و متن‌ها"), KeyboardButton(text="🎨 نام دکمه‌ها")],
        [KeyboardButton(text="📝 ویرایش متن خوش‌آمد"), KeyboardButton(text="📝 ویرایش درباره ما")],
        [KeyboardButton(text="📝 ویرایش قوانین"), KeyboardButton(text="📝 ویرایش FAQ")],
        [KeyboardButton(text="✍️ امضای پیام‌ها"), KeyboardButton(text="🧪 تست رایگان")],
        # ردیف ۷: ارسال و بکاپ
        [KeyboardButton(text="📣 ارسال همگانی"), KeyboardButton(text="💾 بکاپ و ریستور")],
        [KeyboardButton(text=t("back"))],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def admin_main_kb(permissions: list) -> ReplyKeyboardMarkup:
    buttons = []
    perm_buttons = {
        "receipts": KeyboardButton(text="💳 تایید رسیدها"),
        "users": KeyboardButton(text="👥 مدیریت کاربران"),
        "tickets": KeyboardButton(text="💬 تیکت‌ها"),
        "stats": KeyboardButton(text="📊 آمار"),
        "wallet_charge": KeyboardButton(text="💰 شارژ کیف پول"),
        "services": KeyboardButton(text="📦 ایجاد سرویس دستی"),
    }
    row = []
    for perm, btn in perm_buttons.items():
        if "all" in permissions or perm in permissions:
            row.append(btn)
            if len(row) == 2:
                buttons.append(row)
                row = []
    if row:
        buttons.append(row)
    buttons.append([KeyboardButton(text=t("back"))])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def payment_methods_kb(methods: list, amount: int) -> InlineKeyboardMarkup:
    buttons = []
    if "card" in methods:
        buttons.append([InlineKeyboardButton(text="💳 کارت به کارت", callback_data=f"pay:card:{amount}")])
    if "crypto" in methods:
        buttons.append([InlineKeyboardButton(text="₿ ارز دیجیتال", callback_data=f"pay:crypto:{amount}")])
    if "zarinpal" in methods:
        buttons.append([InlineKeyboardButton(text="🏦 درگاه بانکی", callback_data=f"pay:zarinpal:{amount}")])
    buttons.append([InlineKeyboardButton(text=t("cancel"), callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def receipt_review_kb(transaction_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ تایید", callback_data=f"receipt:approve:{transaction_id}"),
            InlineKeyboardButton(text="❌ رد", callback_data=f"receipt:reject:{transaction_id}"),
        ]
    ])

def forced_join_kb(channels: list) -> InlineKeyboardMarkup:
    buttons = []
    for ch in channels:
        link = ch.invite_link or (f"https://t.me/{ch.channel_username}" if ch.channel_username else "#")
        buttons.append([InlineKeyboardButton(text=f"📢 {ch.channel_title or 'عضویت'}", url=link)])
    buttons.append([InlineKeyboardButton(text=t("joined_check"), callback_data="check_join")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def plans_kb(plans: list) -> InlineKeyboardMarkup:
    buttons = []
    for plan in plans:
        text = f"{plan.name} - {int(plan.price):,} تومان"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"plan:{plan.id}")])
    buttons.append([InlineKeyboardButton(text=t("back"), callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def services_kb(services: list) -> InlineKeyboardMarkup:
    buttons = []
    for s in services:
        buttons.append([InlineKeyboardButton(text=f"📦 {s.username}", callback_data=f"srv:{s.id}")])
    buttons.append([InlineKeyboardButton(text=t("back"), callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def tickets_kb(tickets: list) -> InlineKeyboardMarkup:
    buttons = []
    for ticket in tickets:
        status_emoji = {"open": "🟢", "in_progress": "🟡", "closed": "🔴"}.get(ticket.status, "⚪")
        text = f"{status_emoji} #{ticket.id} - {ticket.subject or 'بدون موضوع'}"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"ticket:{ticket.id}")])
    buttons.append([InlineKeyboardButton(text=t("back"), callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)