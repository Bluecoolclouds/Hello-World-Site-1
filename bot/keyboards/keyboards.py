from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

def get_main_menu() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="🔍 Искать"),
        KeyboardButton(text="👤 Профиль"),
        KeyboardButton(text="💌 Чаты")
    )
    return builder.as_markup(resize_keyboard=True)

def get_profile_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="❤️ Лайк", callback_data="like"),
        InlineKeyboardButton(text="💔 Пропустить", callback_data="skip"),
        InlineKeyboardButton(text="☰ Инфо", callback_data="info")
    )
    return builder.as_markup()

def get_chat_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Продолжить", callback_data="continue"),
        InlineKeyboardButton(text="🚫 Заблокировать", callback_data="block"),
        InlineKeyboardButton(text="❌ Удалить", callback_data="delete")
    )
    return builder.as_markup()
