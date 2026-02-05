import time
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.db import Database
from bot.handlers.matching import check_and_notify_match, get_match_keyboard

router = Router()
db = Database()

PHOTO_URL = "https://via.placeholder.com/400x600.png?text=Profile+Photo"

COOLDOWN_SECONDS = 5
HOURLY_LIMIT = 50
HOUR_IN_SECONDS = 3600


def get_search_keyboard(profile_user_id: int) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="❤️ Лайк", callback_data=f"like_{profile_user_id}"),
        InlineKeyboardButton(text="💔 Пропустить", callback_data="skip_profile")
    )
    return kb


def format_profile_text(profile: dict) -> str:
    gender_emoji = "👨" if profile.get('gender') == 'м' else "👩"
    return (
        f"{gender_emoji} Возраст: {profile['age']}\n"
        f"📍 Город: {profile['city']}\n\n"
        f"📝 {profile['bio']}\n\n"
        f"👁 Просмотров: {profile['view_count']}"
    )


def check_cooldown(user: dict, now: float) -> tuple[bool, str]:
    time_since_last = now - user['last_search_at']
    if time_since_last < COOLDOWN_SECONDS:
        remaining = int(COOLDOWN_SECONDS - time_since_last)
        return False, f"⏳ Подождите {remaining} сек. перед следующим поиском."
    return True, ""


def check_hourly_limit(user: dict, now: float) -> tuple[bool, str]:
    time_since_reset = now - user['last_hour_reset']
    if time_since_reset < HOUR_IN_SECONDS and user['search_count_hour'] >= HOURLY_LIMIT:
        minutes_left = int((HOUR_IN_SECONDS - time_since_reset) / 60)
        return False, f"🚫 Лимит просмотров ({HOURLY_LIMIT}/час) исчерпан. Попробуйте через {minutes_left} мин."
    return True, ""


async def search_for_user(user_id: int, message: Message):
    """Поиск анкеты для указанного пользователя"""
    user = db.get_user(user_id)
    
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь! /start")
        return

    now = time.time()
    
    can_search, error_msg = check_cooldown(user, now)
    if not can_search:
        await message.answer(error_msg)
        return
    
    can_search, error_msg = check_hourly_limit(user, now)
    if not can_search:
        await message.answer(error_msg)
        return

    profile = db.get_random_profile(user_id, user['city'], user['preferences'])
    
    if not profile:
        await message.answer(
            "😔 К сожалению, в вашем городе пока нет новых анкет.\n"
            "Попробуйте позже или измените настройки поиска."
        )
        return

    db.update_search_stats(user_id, now)
    db.increment_view_count(profile['user_id'])
    
    profile_text = format_profile_text(profile)
    kb = get_search_keyboard(profile['user_id'])

    await message.answer_photo(
        PHOTO_URL,
        caption=profile_text,
        reply_markup=kb.as_markup()
    )


@router.message(Command("search"))
@router.message(F.text == "🔍 Искать")
async def cmd_search(message: Message):
    await search_for_user(message.from_user.id, message)


@router.callback_query(F.data.startswith("like_"))
async def handle_like(callback: CallbackQuery):
    to_id = int(callback.data.split("_")[1])
    from_id = callback.from_user.id
    
    is_match = db.add_like(from_id, to_id)
    
    if is_match:
        db.create_match(from_id, to_id)
        await check_and_notify_match(callback, from_id, to_id)
    else:
        await callback.answer("💕 Лайк отправлен!")
    
    await show_next_profile(callback)


@router.callback_query(F.data == "skip_profile")
async def handle_skip(callback: CallbackQuery):
    await callback.answer("⏭ Пропущено")
    await show_next_profile(callback)


async def show_next_profile(callback: CallbackQuery):
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await callback.message.answer("❌ Профиль не найден. /start")
        return

    now = time.time()
    
    can_search, error_msg = check_cooldown(user, now)
    if not can_search:
        await callback.message.answer(error_msg)
        return
    
    can_search, error_msg = check_hourly_limit(user, now)
    if not can_search:
        await callback.message.answer(error_msg)
        return

    profile = db.get_random_profile(user_id, user['city'], user['preferences'])
    
    if not profile:
        await callback.message.answer(
            "😔 Анкеты закончились! Возвращайтесь позже."
        )
        return

    db.update_search_stats(user_id, now)
    db.increment_view_count(profile['user_id'])
    
    profile_text = format_profile_text(profile)
    kb = get_search_keyboard(profile['user_id'])

    await callback.message.answer_photo(
        PHOTO_URL,
        caption=profile_text,
        reply_markup=kb.as_markup()
    )


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    user_id = message.from_user.id
    stats = db.get_user_stats(user_id)
    
    if not stats:
        await message.answer("❌ Статистика недоступна. Зарегистрируйтесь: /start")
        return
    
    stats_text = (
        "📊 Ваша статистика:\n\n"
        f"👁 Просмотров вашей анкеты: {stats['view_count']}\n"
        f"❤️ Получено лайков: {stats['likes_received']}\n"
        f"💕 Отправлено лайков: {stats['likes_sent']}\n"
        f"💑 Всего матчей: {stats['matches_count']}\n"
        f"🔍 Поисков за час: {stats['search_count_hour']}/{HOURLY_LIMIT}"
    )
    
    await message.answer(stats_text)
