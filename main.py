
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
    start, user, owner, owner_settings, user_management, support_admin,
    admin, wallet, payment, purchase, support, referral, backup,
    discount, trial, forced_channel, admin_management, plans
)
from middlewares.throttling import ThrottlingMiddleware
from middlewares.auth import AuthMiddleware
from utils.scheduler import setup_scheduler
from utils.texts import load_custom_buttons

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

async def on_startup(bot: Bot):
    logger.info("🚀 PabloVPN-Bot در حال راه‌اندازی...")
    await init_db()
    await load_custom_buttons()
    logger.info("✅ دیتابیس و دکمه‌ها آماده شدند")
    try:
        await bot.send_message(
            config.OWNER_ID,
            "✅ <b>PabloVPN-Bot فعال شد!</b>\n\n🎉 خوش آمدید مالک گرامی."
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

    dp.message.middleware(ThrottlingMiddleware())
    dp.callback_query.middleware(ThrottlingMiddleware())
    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())

    # ترتیب مهم است - هندلرهای تخصصی مالک اول باشند
    dp.include_router(start.router)
    dp.include_router(owner.router)
    dp.include_router(owner_settings.router)
    dp.include_router(user_management.router)
    dp.include_router(support_admin.router)
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
    dp.include_router(user.router)  # آخر باشد

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