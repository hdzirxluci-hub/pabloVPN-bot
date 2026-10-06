import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from config import config

logger = logging.getLogger(__name__)

DATABASE_URL = f"sqlite+aiosqlite:///{config.DATABASE_PATH}"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def init_db():
    from database import models
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await seed_default_settings()
    logger.info("✅ دیتابیس مقداردهی اولیه شد")

async def seed_default_settings():
    from database.models import Setting
    from sqlalchemy import select
    
    defaults = {
        "brand_name": "PabloVPN",
        "welcome_text": "🌟 به {brand} خوش آمدید!\n\nبرای شروع از منوی زیر استفاده کنید.",
        "about_text": "🚀 {brand}\nارائه دهنده سرویس‌های پرسرعت و امن",
        "support_text": "برای ارتباط با پشتیبانی از دکمه زیر استفاده کنید.",
        "rules_text": "قوانین استفاده از سرویس...",
        "channel_lock_enabled": "0",
        "forced_channels": "",
        "card_number": "",
        "card_holder": "",
        "receipt_channel_id": "",
        "support_group_id": "",
        "payment_methods": "card",
        "referral_percent": "10",
        "referral_enabled": "1",
        "free_trial_enabled": "0",
        "free_trial_days": "1",
        "free_trial_gb": "1",
        "min_wallet_charge": "10000",
        "max_wallet_charge": "10000000",
        "backup_schedule": "off",
        "railway_start_date": "",
        "signature": "",
        "logo_file_id": "",
        "faq_text": "❓ سوالات متداول:\n\n۱) چطور خرید کنم؟\nپاسخ: از منوی اصلی گزینه خرید سرویس را انتخاب کنید.",
        "support_offline_text": "⏰ در حال حاضر خارج از ساعات کاری هستیم. پیام شما ثبت شد.",
    }
    
    async with async_session() as session:
        for key, value in defaults.items():
            result = await session.execute(select(Setting).where(Setting.key == key))
            if not result.scalar_one_or_none():
                session.add(Setting(key=key, value=value))
        await session.commit()

async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session