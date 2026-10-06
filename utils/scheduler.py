import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from sqlalchemy import select

from config import config
from database.db import async_session
from database.models import Setting, Service
from utils.texts import get_setting

logger = logging.getLogger(__name__)

async def check_railway_warning(bot: Bot):
    try:
        start_date_str = await get_setting("railway_start_date", "")
        if not start_date_str:
            return
        start_date = datetime.fromisoformat(start_date_str)
        days_passed = (datetime.utcnow() - start_date).days
        days_remaining = config.RAILWAY_TRIAL_DAYS - days_passed
        
        warning_sent_key = f"warning_sent_{days_passed}"
        already_sent = await get_setting(warning_sent_key, "")
        
        if days_passed in config.RAILWAY_WARNING_DAYS and not already_sent:
            text = (
                f"⚠️ <b>هشدار اتمام اعتبار Railway</b>\n\n"
                f"📅 {days_remaining} روز تا اتمام اعتبار باقی مانده!\n\n"
                f"💾 لطفا هر چه زودتر از ربات بکاپ تهیه کنید.\n"
                f"از پنل مالک → 💾 بکاپ و ریستور → دریافت بکاپ"
            )
            try:
                await bot.send_message(config.OWNER_ID, text)
                async with async_session() as session:
                    session.add(Setting(key=warning_sent_key, value="1"))
                    await session.commit()
            except Exception as e:
                logger.error(f"Error sending warning: {e}")
    except Exception as e:
        logger.error(f"Error in railway warning: {e}")

async def auto_backup(bot: Bot):
    try:
        schedule = await get_setting("backup_schedule", "off")
        if schedule == "off":
            return
        from handlers.backup import create_backup_file
        file_path = await create_backup_file()
        if file_path:
            from aiogram.types import FSInputFile
            doc = FSInputFile(file_path)
            await bot.send_document(
                config.OWNER_ID,
                doc,
                caption=f"💾 بکاپ خودکار - {datetime.now().strftime('%Y/%m/%d %H:%M')}"
            )
    except Exception as e:
        logger.error(f"Error in auto backup: {e}")

async def check_expired_services():
    try:
        async with async_session() as session:
            result = await session.execute(
                select(Service).where(
                    Service.is_active == True,
                    Service.expires_at < datetime.utcnow()
                )
            )
            expired = result.scalars().all()
            for service in expired:
                service.is_active = False
            if expired:
                await session.commit()
                logger.info(f"Deactivated {len(expired)} expired services")
    except Exception as e:
        logger.error(f"Error checking expired services: {e}")

def setup_scheduler(scheduler: AsyncIOScheduler, bot: Bot):
    scheduler.add_job(check_railway_warning, "cron", hour=10, args=[bot], id="railway_warning")
    scheduler.add_job(check_expired_services, "interval", hours=1, id="expired_check")
    
    async def backup_job():
        schedule = await get_setting("backup_schedule", "off")
        if schedule == "weekly" and datetime.now().weekday() == 5:
            await auto_backup(bot)
        elif schedule == "biweekly" and datetime.now().weekday() == 5 and (datetime.now().day // 7) % 2 == 0:
            await auto_backup(bot)
        elif schedule == "monthly" and datetime.now().day == 1:
            await auto_backup(bot)
    
    scheduler.add_job(backup_job, "cron", hour=3, minute=0, id="auto_backup")
    logger.info("✅ Scheduler jobs registered")