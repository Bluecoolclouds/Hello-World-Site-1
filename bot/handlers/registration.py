from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, ContentType
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.states.states import Registration, EditProfile
from bot.keyboards.keyboards import get_main_menu
from bot.db import Database, format_online_status

router = Router()
db = Database()


def get_start_keyboard(has_profile: bool) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    if has_profile:
        kb.row(
            InlineKeyboardButton(text="✏️ Изменить", callback_data="show_profile"),
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
        InlineKeyboardButton(text="👨 Парень", callback_data="gender_м"),
        InlineKeyboardButton(text="👩 Девушка", callback_data="gender_ж")
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


def get_looking_for_keyboard() -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="Всё и сразу", callback_data="lookfor_all_now"))
    kb.row(InlineKeyboardButton(text="Без обязательств", callback_data="lookfor_no_strings"))
    kb.row(InlineKeyboardButton(text="Вирт", callback_data="lookfor_virt"))
    kb.row(InlineKeyboardButton(text="Всё серьёзно", callback_data="lookfor_serious"))
    return kb


def get_cancel_keyboard() -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_reg"))
    return kb


def get_skip_photo_keyboard() -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="⏭ Пропустить", callback_data="skip_photo"))
    kb.row(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_reg"))
    return kb


LOOKING_FOR_OPTIONS = {
    'all_now': 'Всё и сразу',
    'no_strings': 'Без обязательств',
    'virt': 'Вирт',
    'serious': 'Всё серьёзно'
}


def format_looking_for(looking_for: str) -> str:
    return LOOKING_FOR_OPTIONS.get(looking_for, 'Не указано')


def format_profile(user: dict) -> str:
    gender_text = "Парень" if user.get('gender') == 'м' else "Девушка"
    pref_text = {
        'м': 'Парни',
        'ж': 'Девушки',
        'все': 'Все'
    }.get(user.get('preferences', 'все'), 'Все')
    
    looking_for_text = format_looking_for(user.get('looking_for', ''))
    online_status = format_online_status(user.get('last_active'))
    
    return (
        f"👤 <b>Ваша анкета:</b>\n\n"
        f"1. 📅 Возраст: {user['age']}\n"
        f"2. ⚧ Пол: {gender_text}\n"
        f"3. 📍 Город: {user['city']}\n"
        f"4. 💬 О себе: {user['bio']}\n"
        f"5. 💕 Кого показывать: {pref_text}\n"
        f"6. 🎯 Я ищу: {looking_for_text}\n"
        f"7. 📷 Фото/видео\n"
        f"{online_status}"
    )


async def send_profile_with_photo(bot, chat_id: int, user: dict, text: str, reply_markup=None):
    photo_id = user.get('photo_id')
    media_type = user.get('media_type', 'photo')
    
    if photo_id:
        try:
            if media_type == 'video':
                await bot.send_video(
                    chat_id=chat_id,
                    video=photo_id,
                    caption=text,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
            elif media_type == 'video_note':
                await bot.send_video_note(chat_id=chat_id, video_note=photo_id)
                await bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
            else:
                await bot.send_photo(
                    chat_id=chat_id,
                    photo=photo_id,
                    caption=text,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
        except Exception:
            await bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
    else:
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode="HTML"
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
        
        await send_profile_with_photo(
            message.bot,
            message.chat.id,
            user,
            f"👋 С возвращением!\n\n{profile_text}",
            kb.as_markup()
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
    
    await send_profile_with_photo(
        callback.bot,
        callback.from_user.id,
        user,
        profile_text,
        kb.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data == "create_profile")
async def create_profile_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Registration.age)
    
    kb = get_cancel_keyboard()
    await callback.message.answer(
        "📝 <b>Создание анкеты</b>\n\n"
        "Сколько тебе лет? (18-60)",
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
    if not message.text or not message.text.isdigit() or not (18 <= int(message.text) <= 60):
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
        "Теперь определимся с полом:",
        reply_markup=kb.as_markup()
    )


@router.callback_query(F.data.startswith("gender_"))
async def process_gender(callback: CallbackQuery, state: FSMContext):
    gender = callback.data.split("_")[1]
    data = await state.get_data()
    
    if data.get('editing_field') == 'gender':
        db.update_user_field(callback.from_user.id, 'gender', gender)
        await state.clear()
        await callback.message.answer("✅ Пол обновлён!")
        await show_updated_profile(callback.bot, callback.from_user.id)
        await callback.answer()
        return
    
    opposite = 'ж' if gender == 'м' else 'м'
    await state.update_data(gender=gender, preferences=opposite, looking_for='')
    await state.set_state(Registration.city)
    
    kb = get_cancel_keyboard()
    await callback.message.edit_text("🏙 Из какого ты города?\n\nНапиши название города:", reply_markup=kb.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("pref_"))
async def process_preferences(callback: CallbackQuery, state: FSMContext):
    pref = callback.data.split("_")[1]
    data = await state.get_data()
    
    if data.get('editing_field') == 'preferences':
        db.update_user_field(callback.from_user.id, 'preferences', pref)
        await state.clear()
        await callback.message.answer("✅ Предпочтения обновлены!")
        await show_updated_profile(callback.bot, callback.from_user.id)
        await callback.answer()
        return
    
    await state.update_data(preferences=pref)
    await state.set_state(Registration.looking_for)
    
    kb = get_looking_for_keyboard()
    await callback.message.edit_text(
        "Что ты ищешь?",
        reply_markup=kb.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("lookfor_"))
async def process_looking_for(callback: CallbackQuery, state: FSMContext):
    looking_for = callback.data.split("_", 1)[1]
    data = await state.get_data()
    
    if data.get('editing_field') == 'looking_for':
        db.update_user_field(callback.from_user.id, 'looking_for', looking_for)
        await state.clear()
        await callback.message.answer("✅ Обновлено!")
        await show_updated_profile(callback.bot, callback.from_user.id)
        await callback.answer()
        return
    
    await state.update_data(looking_for=looking_for)
    await state.set_state(Registration.city)
    
    kb = get_cancel_keyboard()
    await callback.message.edit_text(
        "Из какого ты города?",
        reply_markup=kb.as_markup()
    )
    await callback.answer()


@router.message(Registration.city)
async def process_city(message: Message, state: FSMContext):
    if not message.text or len(message.text) < 2:
        kb = get_cancel_keyboard()
        await message.answer(
            "⚠️ Название города слишком короткое. Введите ещё раз:",
            reply_markup=kb.as_markup()
        )
        return
    
    await state.update_data(city=message.text.strip().title(), bio="Не указано")
    await state.set_state(Registration.photo)
    
    kb = get_skip_photo_keyboard()
    await message.answer(
        "📸 Пришли своё фото или запиши видео (до 15 сек).\n\n"
        "Анкеты, где видно лицо, собирают больше лайков ❤️\n\n"
        "❗️Чужие фото и картинки из интернета не подходят",
        reply_markup=kb.as_markup()
    )


@router.message(Registration.bio)
async def process_bio(message: Message, state: FSMContext):
    bio_text = message.text.strip() if message.text else ""
    
    if bio_text != "-" and len(bio_text) < 3:
        kb = get_cancel_keyboard()
        await message.answer(
            "⚠️ Описание должно быть минимум 3 символа или отправь '-' чтобы пропустить:",
            reply_markup=kb.as_markup()
        )
        return
    
    if bio_text == "-":
        bio_text = "Не указано"
    
    await state.update_data(bio=bio_text)
    await state.set_state(Registration.photo)
    
    kb = get_skip_photo_keyboard()
    await message.answer(
        "📸 Пришли своё фото или запиши видео (до 15 сек).\n\n"
        "Анкеты, где видно лицо, собирают больше лайков ❤️\n\n"
        "❗️Чужие фото и картинки из интернета не подходят",
        reply_markup=kb.as_markup()
    )


@router.message(Registration.photo, F.photo)
async def process_photo(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    await state.update_data(photo_id=photo_id, media_type='photo')
    await finish_registration(message.bot, message.from_user.id, state)


@router.message(Registration.photo, F.video)
async def process_video(message: Message, state: FSMContext):
    if message.video.duration > 15:
        kb = get_skip_photo_keyboard()
        await message.answer(
            "⚠️ Видео должно быть не длиннее 15 секунд. Попробуй ещё раз:",
            reply_markup=kb.as_markup()
        )
        return
    
    video_id = message.video.file_id
    await state.update_data(photo_id=video_id, media_type='video')
    await finish_registration(message.bot, message.from_user.id, state)


@router.message(Registration.photo, F.video_note)
async def process_video_note(message: Message, state: FSMContext):
    video_note_id = message.video_note.file_id
    await state.update_data(photo_id=video_note_id, media_type='video_note')
    await finish_registration(message.bot, message.from_user.id, state)


@router.callback_query(F.data == "skip_photo")
async def skip_photo(callback: CallbackQuery, state: FSMContext):
    await state.update_data(photo_id=None, media_type=None)
    await finish_registration(callback.bot, callback.from_user.id, state)
    await callback.answer()


async def finish_registration(bot, user_id: int, state: FSMContext):
    data = await state.get_data()
    is_editing = data.get('editing')
    
    if is_editing:
        photo_id = data.get('photo_id')
        media_type = data.get('media_type')
        db.update_user_field(user_id, 'photo_id', photo_id)
        db.update_user_field(user_id, 'media_type', media_type)
        await state.clear()
        await bot.send_message(user_id, "✅ Фото/видео обновлено!")
        await show_updated_profile(bot, user_id)
        return
    
    db.save_user(user_id, data)
    await state.clear()
    
    user = db.get_user(user_id)
    profile_text = format_profile(user)
    
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="🔍 Начать поиск", callback_data="start_search")
    )
    
    await send_profile_with_photo(
        bot,
        user_id,
        user,
        f"✅ <b>Анкета создана!</b>\n\n{profile_text}",
        kb.as_markup()
    )


@router.callback_query(F.data == "start_search")
async def start_search_callback(callback: CallbackQuery):
    try:
        from bot.handlers.search import search_for_user_via_bot
        await search_for_user_via_bot(callback.from_user.id, callback.bot)
        await callback.answer()
    except Exception as e:
        import logging
        logging.error(f"Error in start_search: {e}")
        await callback.answer(f"Ошибка: {str(e)[:50]}", show_alert=True)


@router.callback_query(F.data == "edit_profile")
async def edit_profile_callback(callback: CallbackQuery, state: FSMContext):
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="1. 📅 Возраст", callback_data="edit_age"))
    kb.row(InlineKeyboardButton(text="2. ⚧ Пол", callback_data="edit_gender"))
    kb.row(InlineKeyboardButton(text="3. 📍 Город", callback_data="edit_city"))
    kb.row(InlineKeyboardButton(text="4. 💬 О себе", callback_data="edit_bio"))
    kb.row(InlineKeyboardButton(text="5. 💕 Кого показывать", callback_data="edit_pref"))
    kb.row(InlineKeyboardButton(text="6. 🎯 Я ищу", callback_data="edit_looking_for"))
    kb.row(InlineKeyboardButton(text="7. 📷 Фото/видео", callback_data="edit_photo"))
    kb.row(InlineKeyboardButton(text="🔙 Назад", callback_data="show_profile"))
    
    await callback.message.answer(
        "✏️ <b>Что хотите изменить?</b>",
        reply_markup=kb.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data == "edit_photo")
async def edit_photo_callback(callback: CallbackQuery, state: FSMContext):
    await state.update_data(editing=True)
    await state.set_state(Registration.photo)
    
    kb = get_skip_photo_keyboard()
    await callback.message.answer(
        "📸 Пришли новое фото или видео (до 15 сек):",
        reply_markup=kb.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data == "edit_age")
async def edit_age_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(EditProfile.age)
    await callback.message.answer("📅 Введите новый возраст (18-60):")
    await callback.answer()


@router.message(EditProfile.age)
async def process_edit_age(message: Message, state: FSMContext):
    if not message.text or not message.text.isdigit() or not (18 <= int(message.text) <= 60):
        await message.answer("⚠️ Введите корректный возраст (число от 18 до 60):")
        return
    db.update_user_field(message.from_user.id, 'age', int(message.text))
    await state.clear()
    await message.answer("✅ Возраст обновлён!")
    await show_updated_profile(message.bot, message.from_user.id)


@router.callback_query(F.data == "edit_gender")
async def edit_gender_callback(callback: CallbackQuery, state: FSMContext):
    await state.update_data(editing_field='gender')
    kb = get_gender_keyboard()
    await callback.message.answer("⚧ Выберите пол:", reply_markup=kb.as_markup())
    await callback.answer()


@router.callback_query(F.data == "edit_city")
async def edit_city_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(EditProfile.city)
    await callback.message.answer("📍 Введите новый город:")
    await callback.answer()


@router.message(EditProfile.city)
async def process_edit_city(message: Message, state: FSMContext):
    if not message.text or len(message.text) < 2:
        await message.answer("⚠️ Название города слишком короткое. Введите ещё раз:")
        return
    db.update_user_field(message.from_user.id, 'city', message.text.strip().title())
    await state.clear()
    await message.answer("✅ Город обновлён!")
    await show_updated_profile(message.bot, message.from_user.id)


@router.callback_query(F.data == "edit_bio")
async def edit_bio_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(EditProfile.bio)
    await callback.message.answer(
        "💬 Расскажи о себе:\n(минимум 3 символа или '-' чтобы пропустить)"
    )
    await callback.answer()


@router.message(EditProfile.bio)
async def process_edit_bio(message: Message, state: FSMContext):
    bio_text = message.text.strip() if message.text else ""
    if bio_text != "-" and len(bio_text) < 3:
        await message.answer("⚠️ Минимум 3 символа или '-' чтобы пропустить:")
        return
    if bio_text == "-":
        bio_text = "Не указано"
    db.update_user_field(message.from_user.id, 'bio', bio_text)
    await state.clear()
    await message.answer("✅ О себе обновлено!")
    await show_updated_profile(message.bot, message.from_user.id)


@router.callback_query(F.data == "edit_pref")
async def edit_pref_callback(callback: CallbackQuery, state: FSMContext):
    await state.update_data(editing_field='preferences')
    kb = get_preferences_keyboard()
    await callback.message.answer("💕 Кого показывать?", reply_markup=kb.as_markup())
    await callback.answer()


@router.callback_query(F.data == "edit_looking_for")
async def edit_looking_for_callback(callback: CallbackQuery, state: FSMContext):
    await state.update_data(editing_field='looking_for')
    kb = get_looking_for_keyboard()
    await callback.message.answer("🎯 Что ты ищешь?", reply_markup=kb.as_markup())
    await callback.answer()


async def show_updated_profile(bot, user_id: int):
    user = db.get_user(user_id)
    if not user:
        return
    profile_text = format_profile(user)
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="✏️ Изменить", callback_data="edit_profile"),
        InlineKeyboardButton(text="🔍 Искать", callback_data="start_search")
    )
    await send_profile_with_photo(bot, user_id, user, profile_text, kb.as_markup())
