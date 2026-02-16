import os
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))

def get_main_menu(user_id: int = 0) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="🔍 Искать"),
        KeyboardButton(text="👤 Профиль")
    )
    builder.row(
        KeyboardButton(text="💑 Матчи"),
        KeyboardButton(text="💌 Чаты")
    )
    if user_id == ADMIN_USER_ID and ADMIN_USER_ID != 0:
        builder.row(
            KeyboardButton(text="📥 Добавить анкеты")
        )
    return builder.as_markup(resize_keyboard=True)


def get_male_reply_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="Девушки"),
        KeyboardButton(text="Профиль")
    )
    builder.row(
        KeyboardButton(text="Чаты"),
        KeyboardButton(text="Помощь")
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
