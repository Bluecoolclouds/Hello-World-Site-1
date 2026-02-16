import time
import json
import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InputMediaPhoto, InputMediaVideo
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
        InlineKeyboardButton(text="🎁 Подарок", callback_data=f"gift_{profile_user_id}"),
        InlineKeyboardButton(text="💔 Пропустить", callback_data=f"skip_{profile_user_id}")
    )
    return kb


def format_profile_text(profile: dict) -> str:
    from bot.db import format_online_status
    from bot.handlers.registration import format_looking_for
    gender_emoji = "👨" if profile.get('gender') == 'м' else "👩"
    online_status = format_online_status(profile.get('last_active'))
    looking_for_text = format_looking_for(profile.get('looking_for', ''))
    return (
        f"{gender_emoji} Возраст: {profile['age']}\n"
        f"📍 Город: {profile['city']}\n"
        f"🎯 Я ищу: {looking_for_text}\n"
        f"{online_status}\n\n"
        f"📝 {profile['bio']}"
    )


async def send_profile_with_photo(bot, chat_id: int, profile: dict, text: str, reply_markup=None):
    photo_id = profile.get('photo_id')
    media_type = profile.get('media_type', 'photo')
    media_ids_raw = profile.get('media_ids')

    if media_ids_raw:
        try:
            media_list = json.loads(media_ids_raw)
            group = []
            for i, item in enumerate(media_list):
                caption_text = text if i == 0 else None
                if item["type"] == "video":
                    group.append(InputMediaVideo(media=item["id"], caption=caption_text))
                else:
                    group.append(InputMediaPhoto(media=item["id"], caption=caption_text))
            await bot.send_media_group(chat_id=chat_id, media=group)
            if reply_markup:
                await bot.send_message(chat_id=chat_id, text="⬆️", reply_markup=reply_markup)
            return
        except Exception:
            pass

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


def check_cooldown(user: dict, now: float) -> tuple[bool, str]:
    last_search = user.get('last_search_at') or 0
    time_since_last = now - last_search
    if time_since_last < COOLDOWN_SECONDS:
        remaining = int(COOLDOWN_SECONDS - time_since_last)
        return False, f"⏳ Подождите {remaining} сек. перед следующим поиском."
    return True, ""


def check_hourly_limit(user: dict, now: float) -> tuple[bool, str]:
    last_reset = user.get('last_hour_reset') or 0
    search_count = user.get('search_count_hour') or 0
    time_since_reset = now - last_reset
    if time_since_reset < HOUR_IN_SECONDS and search_count >= HOURLY_LIMIT:
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

    min_age = user.get('filter_min_age')
    max_age = user.get('filter_max_age')
    profile = db.get_random_profile(user_id, user['city'], user['preferences'], min_age, max_age)
    
    if not profile:
        await message.answer(
            "Пока нет новых анкет.\n"
            "Попробуйте позже или измените фильтры поиска."
        )
        return

    db.update_search_stats(user_id, now)
    db.increment_view_count(profile['user_id'])
    
    profile_text = format_profile_text(profile)
    kb = get_search_keyboard(profile['user_id'])

    await send_profile_with_photo(message.bot, message.chat.id, profile, profile_text, kb.as_markup())


async def search_for_user_via_bot(user_id: int, bot):
    user = db.get_user(user_id)
    
    if not user:
        await bot.send_message(user_id, "Сначала нажмите /start")
        return

    now = time.time()
    
    can_search, error_msg = check_cooldown(user, now)
    if not can_search:
        await bot.send_message(user_id, error_msg)
        return
    
    can_search, error_msg = check_hourly_limit(user, now)
    if not can_search:
        await bot.send_message(user_id, error_msg)
        return

    min_age = user.get('filter_min_age')
    max_age = user.get('filter_max_age')
    profile = db.get_random_profile(user_id, user['city'], user['preferences'], min_age, max_age)
    
    if not profile:
        await bot.send_message(
            user_id,
            "Пока нет новых анкет.\n"
            "Попробуйте позже или измените фильтры поиска."
        )
        return

    db.update_search_stats(user_id, now)
    db.increment_view_count(profile['user_id'])
    
    profile_text = format_profile_text(profile)
    kb = get_search_keyboard(profile['user_id'])

    await send_profile_with_photo(bot, user_id, profile, profile_text, kb.as_markup())


@router.message(Command("search"))
@router.message(F.text == "🔍 Искать")
async def cmd_search(message: Message):
    await search_for_user(message.from_user.id, message)


@router.callback_query(F.data.regexp(r"^like_\d+$"))
async def handle_like(callback: CallbackQuery):
    to_id = int(callback.data.split("_")[1])
    from_id = callback.from_user.id
    
    is_match = db.add_like(from_id, to_id)
    
    if is_match:
        db.create_match(from_id, to_id)
        await check_and_notify_match(callback, from_id, to_id)
    else:
        await callback.answer("💕 Лайк отправлен!")
        await notify_new_like(callback.bot, to_id, from_id)
    
    await show_next_profile(callback)


async def notify_new_like(bot, to_user_id: int, from_user_id: int):
    """Notify user that someone liked them"""
    try:
        kb = InlineKeyboardBuilder()
        kb.row(
            InlineKeyboardButton(text="👀 Посмотреть кто", callback_data="view_my_likes")
        )
        await bot.send_message(
            to_user_id,
            "💘 Вас кто-то оценил!\n\n"
            "Хотите узнать кто? Нажмите кнопку ниже.",
            reply_markup=kb.as_markup()
        )
    except Exception:
        pass


@router.callback_query(F.data.regexp(r"^skip_\d+$"))
async def handle_skip(callback: CallbackQuery):
    skipped_id = int(callback.data.split("_")[1])
    from_id = callback.from_user.id
    db.add_skip(from_id, skipped_id)
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
        remaining = int(COOLDOWN_SECONDS - (now - (user.get('last_search_at') or 0)))
        wait_msg = await callback.bot.send_message(user_id, error_msg)
        await asyncio.sleep(max(remaining, 1))
        try:
            await wait_msg.delete()
        except Exception:
            pass
        user = db.get_user(user_id)
        now = time.time()
    
    can_search, error_msg = check_hourly_limit(user, now)
    if not can_search:
        await callback.bot.send_message(user_id, error_msg)
        return

    min_age = user.get('filter_min_age')
    max_age = user.get('filter_max_age')
    profile = db.get_random_profile(user_id, user['city'], user['preferences'], min_age, max_age)
    
    if not profile:
        await callback.bot.send_message(
            user_id,
            "Анкеты закончились! Возвращайтесь позже."
        )
        return

    db.update_search_stats(user_id, now)
    db.increment_view_count(profile['user_id'])
    
    profile_text = format_profile_text(profile)
    kb = get_search_keyboard(profile['user_id'])

    await send_profile_with_photo(callback.bot, user_id, profile, profile_text, kb.as_markup())


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
