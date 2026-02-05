from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.db import Database
from bot.keyboards.keyboards import get_main_menu

router = Router()
db = Database()


def get_chat_actions_keyboard(match_user_id: int) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="✅ Продолжить", url=f"tg://user?id={match_user_id}"),
    )
    kb.row(
        InlineKeyboardButton(text="🚫 Заблокировать", callback_data=f"block_{match_user_id}"),
        InlineKeyboardButton(text="❌ Удалить", callback_data=f"delete_match_{match_user_id}")
    )
    return kb


def get_chats_list_keyboard(matches: list) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    for match in matches[:10]:
        match_id = match['matched_user_id']
        user = db.get_user(match_id)
        if user:
            name = f"{user.get('age', '?')}, {user.get('city', '?')}"
            kb.row(
                InlineKeyboardButton(
                    text=f"💬 {name}",
                    callback_data=f"open_chat_{match_id}"
                )
            )
    return kb


@router.message(Command("chats"))
@router.message(F.text == "💌 Чаты")
async def cmd_chats(message: Message):
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь! /start")
        return
    
    matches = db.get_user_matches(user_id)
    
    if not matches:
        await message.answer(
            "💬 У вас пока нет чатов.\n\n"
            "Чтобы начать общение, найдите кого-то и получите взаимный лайк!\n"
            "Используйте /search для поиска."
        )
        return
    
    active_matches = [m for m in matches if not db.is_blocked(user_id, m['matched_user_id'])]
    
    if not active_matches:
        await message.answer(
            "💬 Все ваши чаты заблокированы или удалены.\n"
            "Найдите новых людей: /search"
        )
        return
    
    chats_text = f"💬 Ваши чаты ({len(active_matches)}):\n\n"
    chats_text += "Выберите чат для продолжения общения:"
    
    kb = get_chats_list_keyboard(active_matches)
    await message.answer(chats_text, reply_markup=kb.as_markup())


@router.callback_query(F.data.startswith("open_chat_"))
async def open_chat(callback: CallbackQuery):
    match_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    
    if not db.has_match(user_id, match_id):
        await callback.answer("❌ Этот матч больше недоступен")
        return
    
    if db.is_blocked(user_id, match_id):
        await callback.answer("🚫 Этот пользователь заблокирован")
        return
    
    user = db.get_user(match_id)
    if not user:
        await callback.answer("❌ Профиль не найден")
        return
    
    gender_emoji = "👨" if user.get('gender') == 'м' else "👩"
    chat_text = (
        f"💬 Чат с пользователем:\n\n"
        f"{gender_emoji} Возраст: {user['age']}\n"
        f"📍 Город: {user['city']}\n\n"
        f"📝 {user['bio']}\n\n"
        "Нажмите «Продолжить» чтобы написать."
    )
    
    kb = get_chat_actions_keyboard(match_id)
    await callback.message.answer(chat_text, reply_markup=kb.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("block_"))
async def block_user(callback: CallbackQuery):
    blocked_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    
    db.block_user(user_id, blocked_id)
    
    await callback.message.edit_text(
        "🚫 Пользователь заблокирован.\n\n"
        "Он больше не сможет вам писать и не будет появляться в поиске."
    )
    await callback.answer("Заблокировано")


@router.callback_query(F.data.startswith("delete_match_"))
async def delete_match(callback: CallbackQuery):
    match_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    
    db.delete_match(user_id, match_id)
    
    await callback.message.edit_text(
        "❌ Матч удален.\n\n"
        "Вы можете найти новых людей: /search"
    )
    await callback.answer("Удалено")


@router.callback_query(F.data.startswith("unblock_"))
async def unblock_user(callback: CallbackQuery):
    unblocked_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    
    db.unblock_user(user_id, unblocked_id)
    
    await callback.answer("✅ Пользователь разблокирован")
    await callback.message.answer("✅ Пользователь разблокирован.")


@router.message(Command("blocked"))
async def cmd_blocked(message: Message):
    user_id = message.from_user.id
    blocked = db.get_blocked_users(user_id)
    
    if not blocked:
        await message.answer("📋 Список заблокированных пуст.")
        return
    
    text = f"🚫 Заблокированные пользователи ({len(blocked)}):\n\n"
    
    kb = InlineKeyboardBuilder()
    for b in blocked[:10]:
        user = db.get_user(b['blocked_user_id'])
        if user:
            name = f"{user.get('age', '?')}, {user.get('city', '?')}"
            kb.row(
                InlineKeyboardButton(
                    text=f"🔓 Разблокировать: {name}",
                    callback_data=f"unblock_{b['blocked_user_id']}"
                )
            )
    
    await message.answer(text, reply_markup=kb.as_markup())
