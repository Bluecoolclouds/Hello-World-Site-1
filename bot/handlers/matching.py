from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.db import Database

router = Router()
db = Database()


def get_match_keyboard(user_id: int) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="💬 Написать", url=f"tg://user?id={user_id}")
    )
    return kb


def get_matches_list_keyboard(matches: list) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    for match in matches[:10]:
        match_id = match['matched_user_id']
        name = match.get('username', f"ID: {match_id}")
        kb.row(
            InlineKeyboardButton(
                text=f"💕 {name}", 
                callback_data=f"view_match_{match_id}"
            )
        )
    return kb


async def check_and_notify_match(callback: CallbackQuery, from_id: int, to_id: int):
    from_user = db.get_user(from_id)
    to_user = db.get_user(to_id)
    
    from_kb = get_match_keyboard(to_id)
    await callback.message.answer(
        "🎉 Это МАТЧ! ❤️\n\n"
        f"Вы понравились друг другу!\n"
        f"Напишите первым(ой)!",
        reply_markup=from_kb.as_markup()
    )
    
    try:
        to_kb = get_match_keyboard(from_id)
        bot = callback.bot
        await bot.send_message(
            to_id,
            "🎉 У вас новый МАТЧ! ❤️\n\n"
            "Кто-то ответил вам взаимностью!\n"
            "Не упустите момент!",
            reply_markup=to_kb.as_markup()
        )
    except Exception:
        pass
    
    await callback.answer("💕 Это матч!")


@router.message(Command("matches"))
@router.message(F.text == "💑 Матчи")
async def cmd_matches(message: Message):
    user_id = message.from_user.id
    matches = db.get_user_matches(user_id)
    
    if not matches:
        await message.answer(
            "😔 У вас пока нет матчей.\n\n"
            "Продолжайте искать — ваша пара найдется!\n"
            "Используйте /search для поиска."
        )
        return
    
    matches_text = f"💑 Ваши матчи ({len(matches)}):\n\n"
    
    for i, match in enumerate(matches[:10], 1):
        user = db.get_user(match['matched_user_id'])
        if user:
            matches_text += (
                f"{i}. {user.get('age', '?')} лет, {user.get('city', '?')}\n"
            )
    
    if len(matches) > 10:
        matches_text += f"\n...и еще {len(matches) - 10} матчей"
    
    kb = get_matches_list_keyboard(matches)
    await message.answer(matches_text, reply_markup=kb.as_markup())


@router.callback_query(F.data.startswith("view_match_"))
async def view_match_profile(callback: CallbackQuery):
    match_id = int(callback.data.split("_")[2])
    user = db.get_user(match_id)
    
    if not user:
        await callback.answer("❌ Профиль не найден")
        return
    
    gender_emoji = "👨" if user.get('gender') == 'м' else "👩"
    profile_text = (
        f"💕 Профиль матча:\n\n"
        f"{gender_emoji} Возраст: {user['age']}\n"
        f"📍 Город: {user['city']}\n\n"
        f"📝 {user['bio']}"
    )
    
    kb = get_match_keyboard(match_id)
    await callback.message.answer(profile_text, reply_markup=kb.as_markup())
    await callback.answer()


@router.message(Command("likes"))
async def cmd_likes(message: Message):
    user_id = message.from_user.id
    likes = db.get_received_likes(user_id)
    
    if not likes:
        await message.answer(
            "💔 Пока никто не поставил вам лайк.\n\n"
            "Улучшите профиль или продолжайте искать!"
        )
        return
    
    likes_text = f"❤️ Вас лайкнули ({len(likes)} чел.):\n\n"
    likes_text += "Поставьте лайк в ответ, чтобы создать матч!"
    
    await message.answer(likes_text)
