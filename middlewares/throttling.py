import time
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from config import config

class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self):
        self.last_time: Dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user_id = None
        if isinstance(event, (Message, CallbackQuery)):
            user_id = event.from_user.id
        
        if user_id and user_id != config.OWNER_ID:
            now = time.time()
            last = self.last_time.get(user_id, 0)
            if now - last < config.THROTTLE_RATE:
                if isinstance(event, CallbackQuery):
                    await event.answer("⏳ لطفا کمی صبر کنید...", show_alert=False)
                return
            self.last_time[user_id] = now
        
        return await handler(event, data)