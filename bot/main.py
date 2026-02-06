import asyncio
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.handlers import registration, profile, search, matching, chats, admin, gifts
from bot.db import Database
from bot.middleware import ActivityMiddleware
from bot.scheduler import start_scheduler

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot):
    logger.info("Бот запускается...")
    db = Database()
    logger.info("База данных инициализирована")
    await start_scheduler()
    logger.info("Планировщик задач запущен")


async def on_shutdown(bot: Bot):
    logger.info("Бот останавливается...")


async def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.error("BOT_TOKEN не найден в переменных окружения!")
        logger.error("Создайте файл .env с BOT_TOKEN=your_token_here")
        return
    
    bot = Bot(
        token=token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    
    dp.message.middleware(ActivityMiddleware())
    dp.callback_query.middleware(ActivityMiddleware())

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    dp.include_router(admin.router)
    dp.include_router(registration.router)
    dp.include_router(profile.router)
    dp.include_router(search.router)
    dp.include_router(gifts.router)
    dp.include_router(matching.router)
    dp.include_router(chats.router)

    logger.info("Роутеры подключены")
    logger.info("Бот запущен и готов к работе!")
    
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
