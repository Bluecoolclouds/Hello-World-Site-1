#!/usr/bin/env python3
"""
Запуск Telegram-бота знакомств
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.main import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())
