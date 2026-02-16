from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.db import Database

router = Router()
db = Database()

@router.message(Command("profile"))
async def show_profile(message: Message):
    user = db.get_user(message.from_user.id)
    if not user:
        await message.answer("Профиль не найден. Нажмите /start")
        return

    if user.get('is_girl'):
        from bot.handlers.registration import format_profile, send_profile_with_photo, get_female_menu_keyboard
        profile_text = format_profile(user)
        kb = get_female_menu_keyboard()
        await send_profile_with_photo(message.bot, message.chat.id, user, profile_text, kb.as_markup())
    else:
        from bot.handlers.registration import get_male_menu_keyboard
        kb = get_male_menu_keyboard()
        await message.answer("Главное меню", reply_markup=kb.as_markup())
