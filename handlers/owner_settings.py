from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from utils.decorators import owner_only
from utils.keyboards import owner_main_kb, back_kb
from utils.texts import set_setting, get_setting, clear_cache, set_button, load_custom_buttons, TEXTS, t

router = Router()


class SettingsStates(StatesGroup):
    waiting_welcome = State()
    waiting_about = State()
    waiting_rules = State()
    waiting_support_text = State()
    waiting_faq = State()
    waiting_receipt_channel = State()
    waiting_support_group = State()
    waiting_min_charge = State()
    waiting_max_charge = State()
    waiting_payment_methods = State()
    waiting_trial_toggle = State()
    waiting_trial_days = State()
    waiting_trial_gb = State()
    waiting_referral_percent = State()
    waiting_button_select = State()
    waiting_button_new_text = State()
    waiting_signature = State()


# ============ 📝 ویرایش متن‌ها ============

@router.message(F.text == "📝 ویرایش متن خوش‌آمد")
@owner_only
async def edit_welcome(message: Message, state: FSMContext):
    current = await get_setting("welcome_text", "")
    await state.set_state(SettingsStates.waiting_welcome)
    await message.answer(
        f"📝 متن فعلی:\n\n<code>{current}</code>\n\n"
        f"💡 می‌توانید از <code>{{brand}}</code> برای نام برند استفاده کنید.\n\n"
        f"متن جدید را ارسال کنید:",
        reply_markup=back_kb()
    )

@router.message(SettingsStates.waiting_welcome)
@owner_only
async def save_welcome(message: Message, state: FSMContext):
    if message.text == t("back"):
        await state.clear()
        await message.answer("لغو شد.", reply_markup=owner_main_kb())
        return
    await set_setting("welcome_text", message.text)
    clear_cache()
    await state.clear()
    await message.answer("✅ متن خوش‌آمد ذخیره شد.", reply_markup=owner_main_kb())


@router.message(F.text == "📝 ویرایش درباره ما")
@owner_only
async def edit_about(message: Message, state: FSMContext):
    current = await get_setting("about_text", "")
    await state.set_state(SettingsStates.waiting_about)
    await message.answer(
        f"📝 متن فعلی:\n\n<code>{current}</code>\n\nمتن جدید را ارسال کنید:",
        reply_markup=back_kb()
    )

@router.message(SettingsStates.waiting_about)
@owner_only
async def save_about(message: Message, state: FSMContext):
    if message.text == t("back"):
        await state.clear()
        await message.answer("لغو شد.", reply_markup=owner_main_kb())
        return
    await set_setting("about_text", message.text)
    clear_cache()
    await state.clear()
    await message.answer("✅ متن درباره ما ذخیره شد.", reply_markup=owner_main_kb())


@router.message(F.text == "📝 ویرایش قوانین")
@owner_only
async def edit_rules(message: Message, state: FSMContext):
    current = await get_setting("rules_text", "")
    await state.set_state(SettingsStates.waiting_rules)
    await message.answer(
        f"📝 متن فعلی:\n\n<code>{current}</code>\n\nمتن جدید را ارسال کنید:",
        reply_markup=back_kb()
    )

@router.message(SettingsStates.waiting_rules)
@owner_only
async def save_rules(message: Message, state: FSMContext):
    if message.text == t("back"):
        await state.clear()
        await message.answer("لغو شد.", reply_markup=owner_main_kb())
        return
    await set_setting("rules_text", message.text)
    clear_cache()
    await state.clear()
    await message.answer("✅ قوانین ذخیره شد.", reply_markup=owner_main_kb())


@router.message(F.text == "📝 ویرایش FAQ")
@owner_only
async def edit_faq(message: Message, state: FSMContext):
    current = await get_setting("faq_text", "")
    await state.set_state(SettingsStates.waiting_faq)
    await message.answer(
        f"📝 متن فعلی:\n\n<code>{current}</code>\n\nمتن جدید FAQ را ارسال کنید:",
        reply_markup=back_kb()
    )

@router.message(SettingsStates.waiting_faq)
@owner_only
async def save_faq(message: Message, state: FSMContext):
    if message.text == t("back"):
        await state.clear()
        await message.answer("لغو شد.", reply_markup=owner_main_kb())
        return
    await set_setting("faq_text", message.text)
    clear_cache()
    await state.clear()
    await message.answer("✅ FAQ ذخیره شد.", reply_markup=owner_main_kb())


# ============ 📢 کانال رسید و گروه پشتیبانی ============

@router.message(F.text == "📢 کانال رسید")
@owner_only
async def set_receipt_channel(message: Message, state: FSMContext):
    current = await get_setting("receipt_channel_id", "")
    await state.set_state(SettingsStates.waiting_receipt_channel)
    await message.answer(
        f"📢 <b>تنظیم کانال رسیدها</b>\n\n"
        f"کانال فعلی: <code>{current or 'تنظیم نشده'}</code>\n\n"
        f"📌 مراحل:\n"
        f"۱. یک کانال خصوصی بسازید\n"
        f"۲. ربات را به عنوان ادمین اضافه کنید\n"
        f"۳. آیدی عددی کانال را اینجا بفرستید (مثل <code>-1001234567890</code>)\n\n"
        f"💡 برای گرفتن آیدی کانال، یک پیام در کانال فوروارد کنید به @userinfobot\n\n"
        f"برای حذف کانال فعلی، کلمه <code>remove</code> را بفرستید:",
        reply_markup=back_kb()
    )

@router.message(SettingsStates.waiting_receipt_channel)
@owner_only
async def save_receipt_channel(message: Message, state: FSMContext, bot: Bot):
    if message.text == t("back"):
        await state.clear()
        await message.answer("لغو شد.", reply_markup=owner_main_kb())
        return
    
    text = message.text.strip()
    if text.lower() == "remove":
        await set_setting("receipt_channel_id", "")
        clear_cache()
        await state.clear()
        await message.answer("✅ کانال رسید حذف شد.", reply_markup=owner_main_kb())
        return
    
    try:
        chat = await bot.get_chat(text)
        try:
            test_msg = await bot.send_message(chat.id, "✅ تست اتصال موفق!")
            await bot.delete_message(chat.id, test_msg.message_id)
        except Exception:
            await message.answer("❌ ربات دسترسی به کانال ندارد. لطفا ربات را ادمین کنید.")
            return
        
        await set_setting("receipt_channel_id", str(chat.id))
        clear_cache()
        await state.clear()
        await message.answer(
            f"✅ کانال «{chat.title}» با موفقیت تنظیم شد.\n\n"
            f"از این پس تمام رسیدها به این کانال ارسال می‌شوند.",
            reply_markup=owner_main_kb()
        )
    except Exception as e:
        await message.answer(f"❌ خطا: مطمئن شوید آیدی کانال صحیح است و ربات ادمین است.\n\n<code>{e}</code>")


@router.message(F.text == "💬 گروه پشتیبانی")
@owner_only
async def set_support_group(message: Message, state: FSMContext):
    current = await get_setting("support_group_id", "")
    await state.set_state(SettingsStates.waiting_support_group)
    await message.answer(
        f"💬 <b>تنظیم گروه پشتیبانی</b>\n\n"
        f"گروه فعلی: <code>{current or 'تنظیم نشده'}</code>\n\n"
        f"📌 مراحل:\n"
        f"۱. یک گروه بسازید\n"
        f"۲. ربات را ادمین کنید\n"
        f"۳. آیدی عددی گروه را بفرستید\n\n"
        f"برای حذف، کلمه <code>remove</code> را بفرستید:",
        reply_markup=back_kb()
    )

@router.message(SettingsStates.waiting_support_group)
@owner_only
async def save_support_group(message: Message, state: FSMContext, bot: Bot):
    if message.text == t("back"):
        await state.clear()
        await message.answer("لغو شد.", reply_markup=owner_main_kb())
        return
    
    text = message.text.strip()
    if text.lower() == "remove":
        await set_setting("support_group_id", "")
        clear_cache()
        await state.clear()
        await message.answer("✅ گروه پشتیبانی حذف شد.", reply_markup=owner_main_kb())
        return
    
    try:
        chat = await bot.get_chat(text)
        await set_setting("support_group_id", str(chat.id))
        clear_cache()
        await state.clear()
        await message.answer(f"✅ گروه «{chat.title}» تنظیم شد.", reply_markup=owner_main_kb())
    except Exception as e:
        await message.answer(f"❌ خطا: <code>{e}</code>")


# ============ 💳 روش‌های پرداخت و شارژ ============

@router.message(F.text == "💵 روش‌های پرداخت")
@owner_only
async def payment_methods_menu(message: Message, state: FSMContext):
    current = await get_setting("payment_methods", "card")
    await state.set_state(SettingsStates.waiting_payment_methods)
    await message.answer(
        f"💵 <b>تنظیم روش‌های پرداخت فعال</b>\n\n"
        f"فعلی: <code>{current}</code>\n\n"
        f"روش‌های موجود:\n"
        f"• <code>card</code> - کارت به کارت\n"
        f"• <code>crypto</code> - ارز دیجیتال\n"
        f"• <code>zarinpal</code> - درگاه ریالی\n\n"
        f"چند روش را با کاما جدا کنید.\n"
        f"مثال: <code>card,crypto</code> یا فقط <code>card</code>",
        reply_markup=back_kb()
    )

@router.message(SettingsStates.waiting_payment_methods)
@owner_only
async def save_payment_methods(message: Message, state: FSMContext):
    if message.text == t("back"):
        await state.clear()
        await message.answer("لغو شد.", reply_markup=owner_main_kb())
        return
    
    valid = ["card", "crypto", "zarinpal"]
    chosen = [m.strip().lower() for m in message.text.split(",")]
    final = [m for m in chosen if m in valid]
    
    if not final:
        await message.answer("❌ هیچ روش معتبری انتخاب نشد.")
        return
    
    await set_setting("payment_methods", ",".join(final))
    clear_cache()
    await state.clear()
    await message.answer(f"✅ روش‌های پرداخت تنظیم شد: {', '.join(final)}", reply_markup=owner_main_kb())


@router.message(F.text == "💰 حداقل/حداکثر شارژ")
@owner_only
async def charge_limits(message: Message, state: FSMContext):
    min_c = await get_setting("min_wallet_charge", "10000")
    max_c = await get_setting("max_wallet_charge", "10000000")
    await state.set_state(SettingsStates.waiting_min_charge)
    await message.answer(
        f"💰 <b>محدودیت‌های شارژ کیف پول</b>\n\n"
        f"حداقل فعلی: <code>{int(min_c):,}</code> تومان\n"
        f"حداکثر فعلی: <code>{int(max_c):,}</code> تومان\n\n"
        f"حداقل شارژ جدید را به تومان وارد کنید:",
        reply_markup=back_kb()
    )

@router.message(SettingsStates.waiting_min_charge)
@owner_only
async def save_min_charge(message: Message, state: FSMContext):
    if message.text == t("back"):
        await state.clear()
        await message.answer("لغو شد.", reply_markup=owner_main_kb())
        return
    if not message.text.strip().isdigit():
        await message.answer("❌ لطفا یک عدد صحیح وارد کنید.")
        return
    await set_setting("min_wallet_charge", message.text.strip())
    await state.set_state(SettingsStates.waiting_max_charge)
    await message.answer("حداکثر شارژ را به تومان وارد کنید:")

@router.message(SettingsStates.waiting_max_charge)
@owner_only
async def save_max_charge(message: Message, state: FSMContext):
    if message.text == t("back"):
        await state.clear()
        await message.answer("لغو شد.", reply_markup=owner_main_kb())
        return
    if not message.text.strip().isdigit():
        await message.answer("❌ لطفا یک عدد صحیح وارد کنید.")
        return
    await set_setting("max_wallet_charge", message.text.strip())
    clear_cache()
    await state.clear()
    await message.answer("✅ محدودیت‌های شارژ ذخیره شد.", reply_markup=owner_main_kb())


# ============ 🧪 تست رایگان ============

@router.message(F.text == "🧪 تست رایگان")
@owner_only
async def trial_menu(message: Message, state: FSMContext):
    enabled = await get_setting("free_trial_enabled", "0")
    days = await get_setting("free_trial_days", "1")
    gb = await get_setting("free_trial_gb", "1")
    status = "🟢 فعال" if enabled == "1" else "🔴 غیرفعال"
    
    await state.set_state(SettingsStates.waiting_trial_toggle)
    await message.answer(
        f"🧪 <b>تنظیمات تست رایگان</b>\n\n"
        f"وضعیت: {status}\n"
        f"مدت: {days} روز\n"
        f"حجم: {gb} GB\n\n"
        f"برای فعال/غیرفعال کردن کلمه <code>toggle</code> را بفرستید.\n"
        f"برای تنظیم مدت و حجم کلمه <code>config</code> را بفرستید:",
        reply_markup=back_kb()
    )

@router.message(SettingsStates.waiting_trial_toggle)
@owner_only
async def trial_action(message: Message, state: FSMContext):
    if message.text == t("back"):
        await state.clear()
        await message.answer("لغو شد.", reply_markup=owner_main_kb())
        return
    
    text = message.text.strip().lower()
    if text == "toggle":
        current = await get_setting("free_trial_enabled", "0")
        new = "0" if current == "1" else "1"
        await set_setting("free_trial_enabled", new)
        clear_cache()
        status = "🟢 فعال" if new == "1" else "🔴 غیرفعال"
        await state.clear()
        await message.answer(f"✅ تست رایگان {status} شد.", reply_markup=owner_main_kb())
    elif text == "config":
        await state.set_state(SettingsStates.waiting_trial_days)
        await message.answer("مدت تست رایگان را به روز وارد کنید:")
    else:
        await message.answer("❌ فقط کلمه toggle یا config را بفرستید.")

@router.message(SettingsStates.waiting_trial_days)
@owner_only
async def trial_days_save(message: Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("❌ عدد صحیح وارد کنید.")
        return
    await set_setting("free_trial_days", message.text.strip())
    await state.set_state(SettingsStates.waiting_trial_gb)
    await message.answer("حجم تست رایگان را به گیگابایت وارد کنید:")

@router.message(SettingsStates.waiting_trial_gb)
@owner_only
async def trial_gb_save(message: Message, state: FSMContext):
    try:
        float(message.text)
    except ValueError:
        await message.answer("❌ عدد معتبر وارد کنید.")
        return
    await set_setting("free_trial_gb", message.text.strip())
    clear_cache()
    await state.clear()
    await message.answer("✅ تنظیمات تست رایگان ذخیره شد.", reply_markup=owner_main_kb())


# ============ 👥 درصد زیرمجموعه‌گیری ============

@router.message(F.text == "💹 درصد زیرمجموعه")
@owner_only
async def referral_percent_menu(message: Message, state: FSMContext):
    current = await get_setting("referral_percent", "10")
    await state.set_state(SettingsStates.waiting_referral_percent)
    await message.answer(
        f"💹 <b>تنظیم درصد پاداش زیرمجموعه</b>\n\n"
        f"درصد فعلی: <code>{current}%</code>\n\n"
        f"درصد جدید را وارد کنید (مثلا 15):",
        reply_markup=back_kb()
    )

@router.message(SettingsStates.waiting_referral_percent)
@owner_only
async def save_referral_percent(message: Message, state: FSMContext):
    if message.text == t("back"):
        await state.clear()
        await message.answer("لغو شد.", reply_markup=owner_main_kb())
        return
    text = message.text.strip()
    if not text.isdigit() or not (0 <= int(text) <= 100):
        await message.answer("❌ عدد بین 0 تا 100 وارد کنید.")
        return
    await set_setting("referral_percent", text)
    clear_cache()
    await state.clear()
    await message.answer(f"✅ درصد زیرمجموعه {text}% تنظیم شد.", reply_markup=owner_main_kb())


# ============ 🎨 شخصی‌سازی دکمه‌ها ============

CUSTOMIZABLE_BUTTONS = {
    "user_menu_buy": "🛒 خرید سرویس",
    "user_menu_services": "📦 سرویس‌های من",
    "user_menu_wallet": "👛 کیف پول",
    "user_menu_test": "🎁 تست رایگان",
    "user_menu_referral": "👥 زیرمجموعه‌گیری",
    "user_menu_support": "💬 پشتیبانی",
    "user_menu_guide": "📚 راهنمای اتصال",
    "user_menu_about": "ℹ️ درباره ما",
    "user_menu_rules": "📜 قوانین",
}

@router.message(F.text == "🎨 نام دکمه‌ها")
@owner_only
async def customize_buttons_menu(message: Message, state: FSMContext):
    text = "🎨 <b>شخصی‌سازی نام دکمه‌ها</b>\n\n"
    text += "برای تغییر نام یک دکمه، شماره آن را بفرستید:\n\n"
    
    buttons_list = list(CUSTOMIZABLE_BUTTONS.items())
    for idx, (key, default) in enumerate(buttons_list, start=1):
        current = t(key)
        text += f"<b>{idx}.</b> {current}\n"
    
    await state.set_state(SettingsStates.waiting_button_select)
    await state.update_data(buttons_list=buttons_list)
    await message.answer(text, reply_markup=back_kb())

@router.message(SettingsStates.waiting_button_select)
@owner_only
async def button_select(message: Message, state: FSMContext):
    if message.text == t("back"):
        await state.clear()
        await message.answer("لغو شد.", reply_markup=owner_main_kb())
        return
    
    if not message.text.strip().isdigit():
        await message.answer("❌ لطفا شماره دکمه را وارد کنید.")
        return
    
    idx = int(message.text.strip()) - 1
    data = await state.get_data()
    buttons_list = data.get("buttons_list", [])
    
    if idx < 0 or idx >= len(buttons_list):
        await message.answer("❌ شماره نامعتبر.")
        return
    
    key, default = buttons_list[idx]
    current = t(key)
    await state.update_data(selected_button=key)
    await state.set_state(SettingsStates.waiting_button_new_text)
    await message.answer(
        f"🎨 دکمه انتخابی: <b>{current}</b>\n\n"
        f"نام جدید را ارسال کنید (با ایموجی هم می‌توانید):",
        reply_markup=back_kb()
    )

@router.message(SettingsStates.waiting_button_new_text)
@owner_only
async def button_save_text(message: Message, state: FSMContext):
    if message.text == t("back"):
        await state.clear()
        await message.answer("لغو شد.", reply_markup=owner_main_kb())
        return
    
    data = await state.get_data()
    key = data.get("selected_button")
    new_text = message.text.strip()
    
    await set_button(key, new_text)
    await load_custom_buttons()
    await state.clear()
    await message.answer(
        f"✅ نام دکمه تغییر یافت به: <b>{new_text}</b>\n\n"
        f"💡 با /start جدید منوی به‌روز شده را ببینید.",
        reply_markup=owner_main_kb()
    )


# ============ ✍️ امضا ============

@router.message(F.text == "✍️ امضای پیام‌ها")
@owner_only
async def signature_menu(message: Message, state: FSMContext):
    current = await get_setting("signature", "")
    await state.set_state(SettingsStates.waiting_signature)
    await message.answer(
        f"✍️ <b>تنظیم امضا</b>\n\n"
        f"امضای فعلی: <code>{current or 'ندارد'}</code>\n\n"
        f"امضای جدید را ارسال کنید یا <code>remove</code> برای حذف:",
        reply_markup=back_kb()
    )

@router.message(SettingsStates.waiting_signature)
@owner_only
async def save_signature(message: Message, state: FSMContext):
    if message.text == t("back"):
        await state.clear()
        await message.answer("لغو شد.", reply_markup=owner_main_kb())
        return
    
    text = message.text.strip()
    if text.lower() == "remove":
        await set_setting("signature", "")
    else:
        await set_setting("signature", text)
    
    clear_cache()
    await state.clear()
    await message.answer("✅ امضا ذخیره شد.", reply_markup=owner_main_kb())