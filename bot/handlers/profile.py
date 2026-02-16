from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.db import Database
from bot.keyboards.keyboards import get_main_menu

router = Router()
db = Database()

@router.message(Command("profile"))
async def show_profile(message: Message):
    user = db.get_user(message.from_user.id)
    if not user:
        await message.answer("Профиль не найден. Нажмите /start")
        return

    if user.get('gender') == 'ж':
        from bot.handlers.registration import format_profile, send_profile_with_photo
        profile_text = format_profile(user)
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit_profile"),
            InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")
        )
        await send_profile_with_photo(message.bot, message.chat.id, user, profile_text, builder.as_markup())
    else:
        from bot.handlers.registration import get_male_menu_keyboard
        kb = get_male_menu_keyboard()
        await message.answer("Главное меню", reply_markup=kb.as_markup())

@router.callback_query(F.data == "main_menu")
async def back_to_main(callback):
    await callback.message.answer("Главное меню", reply_markup=get_main_menu(callback.from_user.id))
    await callback.answer()
