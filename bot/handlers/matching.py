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
    from bot.db import format_online_status
    match_id = int(callback.data.split("_")[2])
    user = db.get_user(match_id)
    
    if not user:
        await callback.answer("❌ Профиль не найден")
        return
    
    from bot.handlers.registration import format_looking_for
    gender_emoji = "👨" if user.get('gender') == 'м' else "👩"
    online_status = format_online_status(user.get('last_active'))
    looking_for_text = format_looking_for(user.get('looking_for', ''))
    profile_text = (
        f"💕 Профиль матча:\n\n"
        f"{gender_emoji} Возраст: {user['age']}\n"
        f"📍 Город: {user['city']}\n"
        f"🎯 Я ищу: {looking_for_text}\n"
        f"{online_status}\n\n"
        f"📝 {user['bio']}"
    )
    
    kb = get_match_keyboard(match_id)
    await send_profile_with_photo(callback.bot, callback.from_user.id, user, profile_text, kb.as_markup())
    await callback.answer()


def get_like_review_keyboard(liker_id: int) -> InlineKeyboardBuilder:
    """Keyboard for reviewing incoming likes"""
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="❤️ Лайк", callback_data=f"like_back_{liker_id}"),
        InlineKeyboardButton(text="💔 Пропустить", callback_data=f"skip_liker_{liker_id}")
    )
    return kb


def format_liker_profile(profile: dict) -> str:
    """Format profile text for liker"""
    from bot.db import format_online_status
    from bot.handlers.registration import format_looking_for
    gender_emoji = "👨" if profile.get('gender') == 'м' else "👩"
    online_status = format_online_status(profile.get('last_active'))
    looking_for_text = format_looking_for(profile.get('looking_for', ''))
    return (
        f"💘 Этот человек вас лайкнул!\n\n"
        f"{gender_emoji} Возраст: {profile['age']}\n"
        f"📍 Город: {profile['city']}\n"
        f"🎯 Я ищу: {looking_for_text}\n"
        f"{online_status}\n\n"
        f"📝 {profile['bio']}"
    )


async def send_profile_with_photo(bot, chat_id: int, profile: dict, text: str, reply_markup=None):
    photo_id = profile.get('photo_id')
    media_type = profile.get('media_type', 'photo')
    
    if photo_id:
        try:
            if media_type == 'video':
                await bot.send_video(
                    chat_id=chat_id,
                    video=photo_id,
                    caption=text,
                    reply_markup=reply_markup
                )
            elif media_type == 'video_note':
                await bot.send_video_note(chat_id=chat_id, video_note=photo_id)
                await bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=reply_markup
                )
            else:
                await bot.send_photo(
                    chat_id=chat_id,
                    photo=photo_id,
                    caption=text,
                    reply_markup=reply_markup
                )
        except Exception:
            await bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup
            )
    else:
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup
        )


@router.message(Command("likes"))
async def cmd_likes(message: Message):
    user_id = message.from_user.id
    await show_next_liker(message.bot, user_id)


@router.callback_query(F.data == "view_my_likes")
async def view_my_likes(callback: CallbackQuery):
    user_id = callback.from_user.id
    await callback.answer()
    await show_next_liker(callback.bot, user_id)


async def show_next_liker(bot, user_id: int):
    """Show the next person who liked this user"""
    from bot.handlers.search import search_for_user_via_bot
    likes = db.get_received_likes(user_id)
    
    if not likes:
        await search_for_user_via_bot(user_id, bot)
        return
    
    liker_id = likes[0]['from_user_id']
    liker = db.get_user(liker_id)
    
    if not liker:
        db.remove_like(liker_id, user_id)
        await show_next_liker(bot, user_id)
        return
    
    remaining = len(likes)
    profile_text = format_liker_profile(liker)
    if remaining > 1:
        profile_text += f"\n\n📬 Ещё лайков: {remaining - 1}"
    
    kb = get_like_review_keyboard(liker_id)
    await send_profile_with_photo(bot, user_id, liker, profile_text, kb.as_markup())


@router.callback_query(F.data.startswith("like_back_"))
async def handle_like_back(callback: CallbackQuery):
    """Handle liking back someone who liked you"""
    liker_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    
    is_match = db.add_like(user_id, liker_id)
    
    if is_match:
        db.create_match(user_id, liker_id)
        
        liker = db.get_user(liker_id)
        user = db.get_user(user_id)
        
        kb_to_liker = get_match_keyboard(user_id)
        await callback.message.answer(
            "🎉 Это МАТЧ! ❤️\n\n"
            "Вы понравились друг другу!\n"
            "Напишите первым(ой)!",
            reply_markup=kb_to_liker.as_markup()
        )
        
        try:
            kb_to_user = get_match_keyboard(liker_id)
            await callback.bot.send_message(
                liker_id,
                "🎉 У вас новый МАТЧ! ❤️\n\n"
                "Кто-то ответил вам взаимностью!\n"
                "Не упустите момент!",
                reply_markup=kb_to_user.as_markup()
            )
        except Exception:
            pass
        
        await callback.answer("💕 Это матч!")
    else:
        await callback.answer("💕 Лайк отправлен!")
    
    await show_next_liker(callback.bot, user_id)


@router.callback_query(F.data.startswith("skip_liker_"))
async def handle_skip_liker(callback: CallbackQuery):
    """Skip a liker without liking back"""
    liker_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    
    db.remove_like(liker_id, user_id)
    
    await callback.answer("⏭ Пропущено")
    await show_next_liker(callback.bot, user_id)
