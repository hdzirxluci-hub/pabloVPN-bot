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
    purchase, support, referral, backup
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
    logger.info("🚀 ربات در حال راه‌اندازی...")
    await init_db()
    logger.info("✅ دیتابیس آماده شد")
    try:
        await bot.send_message(
            config.OWNER_ID,
            "✅ ربات با موفقیت راه‌اندازی شد!\n\n🎉 خوش آمدید مالک گرامی"
        )
    except Exception as e:
        logger.warning(f"نتوانست به مالک پیام بفرستد: {e}")

async def on_shutdown(bot: Bot):
    logger.info("🛑 ربات در حال خاموش شدن...")

async def main():
    try:
        config.validate()
    except ValueError as e:
        logger.error(f"خطا: {e}")
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

    dp.include_router(start.router)
    dp.include_router(owner.router)
    dp.include_router(admin.router)
    dp.include_router(backup.router)
    dp.include_router(wallet.router)
    dp.include_router(payment.router)
    dp.include_router(purchase.router)
    dp.include_router(support.router)
    dp.include_router(referral.router)
    dp.include_router(user.router)

    scheduler = AsyncIOScheduler(timezone=config.TIMEZONE)
    setup_scheduler(scheduler, bot)
    scheduler.start()

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("🤖 ربات شروع به کار کرد!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("👋 خداحافظ!")