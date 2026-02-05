import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from bot.handlers import registration, profile, search, example_usage

async def main():
    logging.basicConfig(level=logging.INFO)
    
    # В реальном приложении токен должен быть в .env
    token = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
    bot = Bot(token=token)
    dp = Dispatcher()

    # Регистрация роутеров
    dp.include_router(registration.router)
    dp.include_router(profile.router)
    dp.include_router(search.router)
    dp.include_router(example_usage.router)

    logging.info("Бот запущен")
    # await dp.start_polling(bot) # Закомментировано для примера

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
