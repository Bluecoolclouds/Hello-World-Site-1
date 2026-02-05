import time
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.db import Database
from bot.keyboards.keyboards import get_profile_kb

router = Router()
db = Database()

# Placeholder image URL
PHOTO_URL = "https://via.placeholder.com/400x600.png?text=Profile+Photo"

@router.message(Command("search"))
@router.message(F.text == "🔍 Искать")
async def cmd_search(message: Message):
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message.answer("Сначала зарегистрируйтесь! /start")
        return

    # Проверка лимитов и кулдауна
    now = time.time()
    if now - user['last_search_at'] < 5:
        await message.answer("Подождите 5 секунд перед следующим поиском.")
        return
    
    if now - user['last_hour_reset'] < 3600 and user['search_count_hour'] >= 50:
        await message.answer("Вы достигли лимита просмотров (50 в час).")
        return

    profile = db.get_random_profile(user_id, user['city'], user['preferences'])
    
    if not profile:
        await message.answer("К сожалению, в вашем городе пока нет новых анкет.")
        return

    db.update_search_stats(user_id, now)
    
    profile_text = (
        f"👤 {profile['age']}, {profile['city']}\n\n"
        f"📝 {profile['bio']}\n\n"
        f"📊 Просмотров анкеты: {profile['view_count']}"
    )

    kb = InlineKeyboardBuilder()
    kb.row(
        F.InlineKeyboardButton(text="❤️ Лайк", callback_data=f"like_{profile['user_id']}"),
        F.InlineKeyboardButton(text="💔 Пропустить", callback_data="skip_profile")
    )

    await message.answer_photo(
        PHOTO_URL,
        caption=profile_text,
        reply_markup=kb.as_markup()
    )

@router.callback_query(F.data.startswith("like_"))
async def handle_like(callback: CallbackQuery, bot):
    to_id = int(callback.data.split("_")[1])
    from_id = callback.from_user.id
    
    is_match = db.add_like(from_id, to_id)
    
    if is_match:
        # Уведомление текущему пользователю
        await callback.message.answer(
            "Это МАТЧ! ❤️ Вы понравились друг другу.",
            reply_markup=InlineKeyboardBuilder().row(
                F.InlineKeyboardButton(text="Написать", url=f"tg://user?id={to_id}")
            ).as_markup()
        )
        
        # Уведомление второму пользователю
        try:
            await bot.send_message(
                to_id,
                "У вас новый МАТЧ! ❤️ Посмотрите, кто вам ответил взаимностью.",
                reply_markup=InlineKeyboardBuilder().row(
                    F.InlineKeyboardButton(text="Написать", url=f"tg://user?id={from_id}")
                ).as_markup()
            )
        except Exception:
            pass # Пользователь мог заблокировать бота
            
    await callback.answer("Лайк отправлен!")
    await cmd_search(callback.message) # Показываем следующего

@router.callback_query(F.data == "skip_profile")
async def handle_skip(callback: CallbackQuery):
    await callback.answer("Пропущено")
    await cmd_search(callback.message)
