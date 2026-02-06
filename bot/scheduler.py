import asyncio
import random
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


async def fake_users_online_task():
    """Каждые ~2 часа случайно обновляет last_active у части fake-профилей"""
    while True:
        try:
            updated = db.touch_random_fake_users()
            if updated > 0:
                logger.info(f"Fake-онлайн: обновлено {updated} fake-профилей")
        except Exception as e:
            logger.error(f"Ошибка fake-онлайн: {e}")
        
        delay = random.randint(6000, 8400)
        await asyncio.sleep(delay)


async def start_scheduler():
    """Запуск планировщика задач"""
    logger.info("Планировщик задач запущен")
    asyncio.create_task(archive_inactive_users_task())
    asyncio.create_task(fake_users_online_task())
