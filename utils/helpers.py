import re
import secrets
import string
from datetime import datetime, timedelta
from sqlalchemy import select
from database.db import async_session
from database.models import User
from config import config

def generate_random_string(length: int = 8) -> str:
    chars = string.ascii_lowercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))

def generate_username(telegram_id: int) -> str:
    return f"u{telegram_id}_{generate_random_string(6)}"

def format_price(amount: float) -> str:
    return f"{int(amount):,}"

def format_bytes(gb: float) -> str:
    if gb >= 1000:
        return f"{gb/1000:.1f} TB"
    return f"{gb} GB"

def format_date(dt: datetime) -> str:
    if not dt:
        return "-"
    return dt.strftime("%Y/%m/%d %H:%M")

def days_until(dt: datetime) -> int:
    if not dt:
        return 0
    delta = dt - datetime.utcnow()
    return max(0, delta.days)

def is_valid_amount(text: str) -> int:
    text = text.strip().replace(",", "").replace("،", "")
    if not text.isdigit():
        return 0
    return int(text)

def parse_card_number(text: str) -> str:
    digits = re.sub(r'\D', '', text)
    if len(digits) == 16:
        return ' '.join(digits[i:i+4] for i in range(0, 16, 4))
    return text

async def get_or_create_user(telegram_id: int, username: str = None, first_name: str = None, referrer_id: int = None) -> User:
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if user:
            updated = False
            if username and user.username != username:
                user.username = username
                updated = True
            if first_name and user.first_name != first_name:
                user.first_name = first_name
                updated = True
            user.last_activity = datetime.utcnow()
            if updated:
                await session.commit()
            return user
        is_owner = telegram_id == config.OWNER_ID
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            referrer_id=referrer_id if referrer_id and referrer_id != telegram_id else None,
            is_admin=is_owner,
            admin_permissions="all" if is_owner else "",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

async def is_owner(telegram_id: int) -> bool:
    return telegram_id == config.OWNER_ID

async def is_admin(telegram_id: int) -> bool:
    if telegram_id == config.OWNER_ID:
        return True
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        return user.is_admin if user else False

async def get_admin_permissions(telegram_id: int) -> list:
    if telegram_id == config.OWNER_ID:
        return ["all", "receipts", "users", "tickets", "stats", "wallet_charge", "services"]
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if not user or not user.is_admin:
            return []
        if user.admin_permissions == "all":
            return ["all", "receipts", "users", "tickets", "stats", "wallet_charge", "services"]
        return user.admin_permissions.split(",") if user.admin_permissions else []

async def has_permission(telegram_id: int, permission: str) -> bool:
    perms = await get_admin_permissions(telegram_id)
    return "all" in perms or permission in perms

def escape_html(text: str) -> str:
    if not text:
        return ""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def extract_referrer_from_start(args: str) -> int:
    if not args:
        return None
    match = re.search(r'ref_?(\d+)', args)
    if match:
        return int(match.group(1))
    if args.isdigit():
        return int(args)
    return None