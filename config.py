import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    OWNER_ID = int(os.getenv("OWNER_ID", "0"))
    DATABASE_PATH = os.getenv("DATABASE_PATH", "database.db")
    TIMEZONE = os.getenv("TIMEZONE", "Asia/Tehran")
    
    DEFAULT_BRAND_NAME = "PabloVPN"
    DEFAULT_WELCOME_TEXT = "🌟 به {brand} خوش آمدید!\n\nبرای شروع از منوی زیر استفاده کنید."
    DEFAULT_ABOUT_TEXT = "🚀 {brand}\nارائه دهنده سرویس‌های پرسرعت و امن"
    DEFAULT_SUPPORT_TEXT = "برای ارتباط با پشتیبانی از دکمه زیر استفاده کنید."
    
    BACKUP_DIR = "backups"
    MAX_BACKUP_FILES = 10
    
    RAILWAY_TRIAL_DAYS = 30
    RAILWAY_WARNING_DAYS = [25, 28, 29]
    
    THROTTLE_RATE = 0.5
    
    @classmethod
    def validate(cls):
        errors = []
        if not cls.BOT_TOKEN:
            errors.append("❌ BOT_TOKEN تنظیم نشده!")
        if not cls.OWNER_ID:
            errors.append("❌ OWNER_ID تنظیم نشده!")
        if errors:
            for e in errors:
                print(e)
            raise ValueError("تنظیمات ناقص!")
        return True

config = Config()