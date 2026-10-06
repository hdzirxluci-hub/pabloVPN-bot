from functools import wraps
from aiogram.types import Message, CallbackQuery
from utils.helpers import is_owner, is_admin, has_permission
from utils.texts import t

def owner_only(func):
    @wraps(func)
    async def wrapper(event, *args, **kwargs):
        user_id = event.from_user.id
        if not await is_owner(user_id):
            if isinstance(event, CallbackQuery):
                await event.answer(t("unauthorized"), show_alert=True)
            else:
                await event.answer(t("unauthorized"))
            return
        return await func(event, *args, **kwargs)
    return wrapper

def admin_only(func):
    @wraps(func)
    async def wrapper(event, *args, **kwargs):
        user_id = event.from_user.id
        if not await is_admin(user_id):
            if isinstance(event, CallbackQuery):
                await event.answer(t("unauthorized"), show_alert=True)
            else:
                await event.answer(t("unauthorized"))
            return
        return await func(event, *args, **kwargs)
    return wrapper

def require_permission(permission: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(event, *args, **kwargs):
            user_id = event.from_user.id
            if not await has_permission(user_id, permission):
                if isinstance(event, CallbackQuery):
                    await event.answer(t("unauthorized"), show_alert=True)
                else:
                    await event.answer(t("unauthorized"))
                return
            return await func(event, *args, **kwargs)
        return wrapper
    return decorator