from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.db import Database
from bot.keyboards.keyboards import get_main_menu

router = Router()
db = Database()

@router.message(Command("profile"))
@router.message(F.text == "👤 Профиль")
async def show_profile(message: Message):
    user = db.get_user(message.from_user.id)
    if not user:
        await message.answer("Ваш профиль не найден. Пройдите регистрацию: /start")
        return

    profile_text = (
        f"👤 Ваш профиль:\n\n"
        f"Возраст: {user['age']}\n"
        f"Пол: {user['gender']}\n"
        f"Город: {user['city']}\n"
        f"О себе: {user['bio']}\n"
        f"Предпочтения: {user['preferences']}"
    )

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📝 Редактировать", callback_data="edit_profile"),
        InlineKeyboardButton(text="🏠 Главная", callback_data="main_menu")
    )

    await message.answer(profile_text, reply_markup=builder.as_markup())

@router.callback_query(F.data == "main_menu")
async def back_to_main(callback):
    await callback.message.answer("Главное меню", reply_markup=get_main_menu(callback.from_user.id))
    await callback.answer()
