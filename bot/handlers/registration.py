from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.states.states import Registration
from bot.keyboards.keyboards import get_main_menu
from bot.db import Database

router = Router()
db = Database()

PHOTO_URL = "https://via.placeholder.com/400x600.png?text=Profile+Photo"


def get_start_keyboard(has_profile: bool) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    if has_profile:
        kb.row(
            InlineKeyboardButton(text="👤 Моя анкета", callback_data="show_profile"),
            InlineKeyboardButton(text="🔍 Искать", callback_data="start_search")
        )
    else:
        kb.row(
            InlineKeyboardButton(text="📝 Создать анкету", callback_data="create_profile")
        )
    return kb


def get_gender_keyboard() -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="👨 Мужской", callback_data="gender_м"),
        InlineKeyboardButton(text="👩 Женский", callback_data="gender_ж")
    )
    return kb


def get_preferences_keyboard() -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="👨 Парней", callback_data="pref_м"),
        InlineKeyboardButton(text="👩 Девушек", callback_data="pref_ж")
    )
    kb.row(
        InlineKeyboardButton(text="👥 Всех", callback_data="pref_все")
    )
    return kb


def get_cancel_keyboard() -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_reg"))
    return kb


def format_profile(user: dict) -> str:
    gender_text = "Мужской" if user.get('gender') == 'м' else "Женский"
    pref_text = {
        'м': 'Парни',
        'ж': 'Девушки',
        'все': 'Все'
    }.get(user.get('preferences', 'все'), 'Все')
    
    return (
        f"👤 <b>Ваша анкета:</b>\n\n"
        f"📅 Возраст: {user['age']}\n"
        f"⚧ Пол: {gender_text}\n"
        f"📍 Город: {user['city']}\n"
        f"💬 О себе: {user['bio']}\n"
        f"💕 Ищу: {pref_text}\n\n"
        f"👁 Просмотров: {user.get('view_count', 0)}"
    )


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = db.get_user(message.from_user.id)
    
    if user:
        if db.is_banned(message.from_user.id):
            await message.answer("🚫 Ваш аккаунт заблокирован.")
            return
        
        profile_text = format_profile(user)
        kb = get_start_keyboard(has_profile=True)
        
        await message.answer_photo(
            PHOTO_URL,
            caption=f"👋 С возвращением!\n\n{profile_text}",
            reply_markup=kb.as_markup()
        )
    else:
        welcome_text = (
            "👋 <b>Добро пожаловать в бот знакомств!</b>\n\n"
            "Здесь вы можете найти новых друзей или вторую половинку.\n\n"
            "Для начала создайте свою анкету!"
        )
        kb = get_start_keyboard(has_profile=False)
        await message.answer(welcome_text, reply_markup=kb.as_markup())


@router.callback_query(F.data == "show_profile")
async def show_profile_callback(callback: CallbackQuery):
    user = db.get_user(callback.from_user.id)
    if not user:
        await callback.answer("Анкета не найдена")
        return
    
    profile_text = format_profile(user)
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="✏️ Изменить", callback_data="edit_profile"),
        InlineKeyboardButton(text="🔍 Искать", callback_data="start_search")
    )
    
    await callback.message.answer_photo(
        PHOTO_URL,
        caption=profile_text,
        reply_markup=kb.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data == "create_profile")
async def create_profile_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Registration.age)
    
    kb = get_cancel_keyboard()
    await callback.message.answer(
        "📝 <b>Создание анкеты</b>\n\n"
        "Шаг 1/5: Введите ваш возраст (18-60):",
        reply_markup=kb.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data == "cancel_reg")
async def cancel_registration(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "❌ Регистрация отменена.\n\n"
        "Используйте /start чтобы начать заново."
    )
    await callback.answer("Отменено")


@router.message(Command("cancel"))
@router.message(F.text.casefold() == "отмена")
async def cancel_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return

    await state.clear()
    await message.answer(
        "❌ Регистрация отменена. Используйте /start, чтобы начать заново."
    )


@router.message(Registration.age)
async def process_age(message: Message, state: FSMContext):
    if not message.text.isdigit() or not (18 <= int(message.text) <= 60):
        kb = get_cancel_keyboard()
        await message.answer(
            "⚠️ Введите корректный возраст (число от 18 до 60):",
            reply_markup=kb.as_markup()
        )
        return
    
    await state.update_data(age=int(message.text), username=message.from_user.username)
    await state.set_state(Registration.gender)
    
    kb = get_gender_keyboard()
    await message.answer(
        "📝 <b>Создание анкеты</b>\n\n"
        "Шаг 2/5: Выберите ваш пол:",
        reply_markup=kb.as_markup()
    )


@router.callback_query(F.data.startswith("gender_"))
async def process_gender(callback: CallbackQuery, state: FSMContext):
    gender = callback.data.split("_")[1]
    await state.update_data(gender=gender)
    await state.set_state(Registration.city)
    
    kb = get_cancel_keyboard()
    await callback.message.edit_text(
        "📝 <b>Создание анкеты</b>\n\n"
        "Шаг 3/5: Из какого вы города?",
        reply_markup=kb.as_markup()
    )
    await callback.answer()


@router.message(Registration.city)
async def process_city(message: Message, state: FSMContext):
    if len(message.text) < 2:
        kb = get_cancel_keyboard()
        await message.answer(
            "⚠️ Название города слишком короткое. Введите ещё раз:",
            reply_markup=kb.as_markup()
        )
        return
    
    await state.update_data(city=message.text.strip().title())
    await state.set_state(Registration.bio)
    
    kb = get_cancel_keyboard()
    await message.answer(
        "📝 <b>Создание анкеты</b>\n\n"
        "Шаг 4/5: Расскажите о себе (или отправьте '-' чтобы пропустить):",
        reply_markup=kb.as_markup()
    )


@router.message(Registration.bio)
async def process_bio(message: Message, state: FSMContext):
    bio_text = message.text.strip() if message.text else ""
    
    if bio_text and len(bio_text) < 3:
        kb = get_cancel_keyboard()
        await message.answer(
            "⚠️ Био должно быть минимум 3 символа или оставьте пустым (отправьте '-'):",
            reply_markup=kb.as_markup()
        )
        return
    
    if bio_text == "-":
        bio_text = ""
    
    await state.update_data(bio=bio_text if bio_text else "Не указано")
    await state.set_state(Registration.preferences)
    
    kb = get_preferences_keyboard()
    await message.answer(
        "📝 <b>Создание анкеты</b>\n\n"
        "Шаг 5/5: Кого вы ищете?",
        reply_markup=kb.as_markup()
    )


@router.callback_query(F.data.startswith("pref_"))
async def process_preferences(callback: CallbackQuery, state: FSMContext):
    pref = callback.data.split("_")[1]
    await state.update_data(preferences=pref)
    
    data = await state.get_data()
    db.save_user(callback.from_user.id, data)
    await state.clear()
    
    user = db.get_user(callback.from_user.id)
    profile_text = format_profile(user)
    
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="🔍 Начать поиск", callback_data="start_search")
    )
    
    await callback.message.edit_text("✅ Анкета создана!")
    
    await callback.bot.send_photo(
        chat_id=callback.from_user.id,
        photo=PHOTO_URL,
        caption=f"✅ <b>Анкета создана!</b>\n\n{profile_text}",
        reply_markup=kb.as_markup()
    )
    await callback.answer("Регистрация завершена!")


@router.callback_query(F.data == "start_search")
async def start_search_callback(callback: CallbackQuery):
    from bot.handlers.search import search_for_user_via_bot
    await search_for_user_via_bot(callback.from_user.id, callback.bot)
    await callback.answer()


@router.callback_query(F.data == "edit_profile")
async def edit_profile_callback(callback: CallbackQuery, state: FSMContext):
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="📅 Возраст", callback_data="edit_age"),
        InlineKeyboardButton(text="📍 Город", callback_data="edit_city")
    )
    kb.row(
        InlineKeyboardButton(text="💬 О себе", callback_data="edit_bio"),
        InlineKeyboardButton(text="💕 Предпочтения", callback_data="edit_pref")
    )
    kb.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="show_profile")
    )
    
    await callback.message.answer(
        "✏️ <b>Что хотите изменить?</b>",
        reply_markup=kb.as_markup()
    )
    await callback.answer()
