import asyncio
import logging
from datetime import datetime, timedelta

from bot.db import Database

logger = logging.getLogger(__name__)
db = Database()


async def archive_inactive_users_task():
    """Ежедневная задача архивации неактивных пользователей"""
    while True:
        try:
            archived_count = db.archive_inactive_users(days=7)
            logger.info(f"Ежедневная архивация: {archived_count} пользователей архивировано")
        except Exception as e:
            logger.error(f"Ошибка при архивации: {e}")
        
        await asyncio.sleep(86400)


async def start_scheduler():
    """Запуск планировщика задач"""
    logger.info("Планировщик задач запущен")
    asyncio.create_task(archive_inactive_users_task())
