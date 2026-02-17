import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

from bot.db import Database

logger = logging.getLogger(__name__)
db = Database()


class ActivityMiddleware(BaseMiddleware):
    """Middleware для обновления last_active при каждом взаимодействии"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user_id = None
        
        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else None
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id if event.from_user else None
        
        if user_id:
            try:
                user = db.get_user(user_id)
                if user:
                    db.update_last_active(user_id)
                    
                    if user.get('is_archived'):
                        db.unarchive_user(user_id)
                        logger.info(f"Пользователь {user_id} автоматически разархивирован")
            except Exception as e:
                logger.error(f"Ошибка в ActivityMiddleware: {e}")
        
        if isinstance(event, Message):
            logger.info(f"[MSG] user={event.from_user.id} text={event.text!r} state={data.get('raw_state')}")
        elif isinstance(event, CallbackQuery):
            logger.info(f"[CB] user={event.from_user.id} data={event.data!r}")
        
        result = await handler(event, data)
        return result
