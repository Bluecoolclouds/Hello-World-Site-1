import json
import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, ContentType, InputMediaPhoto, InputMediaVideo
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.states.states import Registration, EditProfile, FilterState
from bot.keyboards.keyboards import get_main_menu
from bot.db import Database, format_online_status

router = Router()
db = Database()

ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))

LOOKING_FOR_OPTIONS = {
    'all_now': 'Все и сразу',
    'no_strings': 'Без обязательств',
    'virt': 'Вирт',
    'serious': 'Все серьезно'
}


def format_looking_for(looking_for: str) -> str:
    return LOOKING_FOR_OPTIONS.get(looking_for, 'Не указано')


def get_male_menu_keyboard() -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="🔍 Смотреть анкеты", callback_data="start_search"))
    kb.row(InlineKeyboardButton(text="⚙️ Фильтры поиска", callback_data="open_filters"))
    kb.row(InlineKeyboardButton(text="📊 Статистика", callback_data="show_stats"))
    return kb


def get_female_menu_keyboard() -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="👤 Моя анкета", callback_data="show_profile"))
    kb.row(InlineKeyboardButton(text="✏️ Редактировать анкету", callback_data="edit_profile"))
    kb.row(InlineKeyboardButton(text="💑 Мои матчи", callback_data="show_matches"))
    return kb


def get_filter_keyboard(user: dict) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    min_age = user.get('filter_min_age')
    max_age = user.get('filter_max_age')
    age_text = "Любой"
    if min_age and max_age:
        age_text = f"{min_age}-{max_age}"
    elif min_age:
        age_text = f"от {min_age}"
    elif max_age:
        age_text = f"до {max_age}"
    kb.row(InlineKeyboardButton(text=f"📅 Возраст: {age_text}", callback_data="filter_age"))
    kb.row(InlineKeyboardButton(text="🗑 Сбросить фильтры", callback_data="filter_reset"))
    kb.row(InlineKeyboardButton(text="🔍 Начать поиск", callback_data="start_search"))
    kb.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main"))
    return kb


def format_profile(user: dict) -> str:
    gender_text = "Парень" if user.get('gender') == 'м' else "Девушка"
    pref_text = {
        'м': 'Парни',
        'ж': 'Девушки',
        'все': 'Все'
    }.get(user.get('preferences', 'все'), 'Все')

    looking_for_text = format_looking_for(user.get('looking_for', ''))
    online_status = format_online_status(user.get('last_active'))
    bio = user.get('bio', 'Не указано')

    lines = [f"👤 <b>Анкета:</b>\n"]
    lines.append(f"1. Возраст: {user['age']}")
    lines.append(f"2. Пол: {gender_text}")
    lines.append(f"3. Город: {user['city']}")

    if bio and bio != "Не указано" and bio != "":
        lines.append(f"4. О себе: {bio}")
    else:
        lines.append(f"4. О себе: Не указано")

    lines.append(f"5. Кого показывать: {pref_text}")

    if looking_for_text and looking_for_text != "Не указано":
        lines.append(f"6. Я ищу: {looking_for_text}")
    else:
        lines.append(f"6. Я ищу: Не указано")

    lines.append(f"7. Фото/видео")
    lines.append(online_status)

    return "\n".join(lines)


async def send_profile_with_photo(bot, chat_id: int, user: dict, text: str, reply_markup=None):
    photo_id = user.get('photo_id')
    media_type = user.get('media_type', 'photo')
    media_ids_raw = user.get('media_ids')

    if media_ids_raw:
        try:
            media_list = json.loads(media_ids_raw)
            group = []
            for i, item in enumerate(media_list):
                caption_text = text if i == 0 else None
                if item["type"] == "video":
                    group.append(InputMediaVideo(media=item["id"], caption=caption_text, parse_mode="HTML"))
                else:
                    group.append(InputMediaPhoto(media=item["id"], caption=caption_text, parse_mode="HTML"))
            await bot.send_media_group(chat_id=chat_id, media=group)
            if reply_markup:
                await bot.send_message(chat_id=chat_id, text="⬆️", reply_markup=reply_markup, parse_mode="HTML")
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
    user_id = message.from_user.id
    user = db.get_user(user_id)

    if user:
        if db.is_banned(user_id):
            await message.answer("Ваш аккаунт заблокирован.")
            return

        if user.get('gender') == 'ж':
            profile_text = format_profile(user)
            kb = get_female_menu_keyboard()
            await send_profile_with_photo(
                message.bot,
                message.chat.id,
                user,
                f"С возвращением!\n\n{profile_text}",
                kb.as_markup()
            )
        else:
            kb = get_male_menu_keyboard()
            await message.answer(
                "<b>Добро пожаловать!</b>\n\n"
                "Нажмите кнопку ниже, чтобы начать просмотр анкет.",
                reply_markup=kb.as_markup()
            )
    else:
        db.create_male_user(user_id, message.from_user.username)
        kb = get_male_menu_keyboard()
        await message.answer(
            "<b>Добро пожаловать!</b>\n\n"
            "Нажмите кнопку ниже, чтобы начать просмотр анкет.",
            reply_markup=kb.as_markup()
        )


@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user = db.get_user(callback.from_user.id)
    if user and user.get('gender') == 'ж':
        kb = get_female_menu_keyboard()
        await callback.message.answer("Главное меню", reply_markup=kb.as_markup())
    else:
        kb = get_male_menu_keyboard()
        await callback.message.answer("Главное меню", reply_markup=kb.as_markup())
    await callback.answer()


@router.callback_query(F.data == "show_stats")
async def show_stats_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    stats = db.get_user_stats(user_id)
    if not stats:
        await callback.answer("Статистика недоступна")
        return

    stats_text = (
        "<b>Ваша статистика:</b>\n\n"
        f"Получено лайков: {stats['likes_received']}\n"
        f"Отправлено лайков: {stats['likes_sent']}\n"
        f"Всего матчей: {stats['matches_count']}\n"
        f"Поисков за час: {stats['search_count_hour']}/50"
    )
    await callback.message.answer(stats_text)
    await callback.answer()


@router.callback_query(F.data == "open_filters")
async def open_filters(callback: CallbackQuery):
    user = db.get_user(callback.from_user.id)
    if not user:
        await callback.answer("Ошибка")
        return
    kb = get_filter_keyboard(user)
    await callback.message.answer(
        "<b>Фильтры поиска:</b>\n\n"
        "Настройте параметры поиска анкет.",
        reply_markup=kb.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data == "filter_age")
async def filter_age(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FilterState.min_age)
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="Отмена", callback_data="back_to_main"))
    await callback.message.answer(
        "Введите <b>минимальный</b> возраст (18-60):\n\n"
        "Или отправьте <b>-</b> чтобы не ограничивать.",
        reply_markup=kb.as_markup()
    )
    await callback.answer()


@router.message(FilterState.min_age)
async def process_filter_min_age(message: Message, state: FSMContext):
    text = message.text.strip() if message.text else ""
    if text == "-":
        await state.update_data(filter_min_age=None)
    elif text.isdigit() and 18 <= int(text) <= 60:
        await state.update_data(filter_min_age=int(text))
    else:
        await message.answer("Введите число от 18 до 60 или <b>-</b> чтобы пропустить:")
        return

    await state.set_state(FilterState.max_age)
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="Отмена", callback_data="back_to_main"))
    await message.answer(
        "Введите <b>максимальный</b> возраст (18-60):\n\n"
        "Или отправьте <b>-</b> чтобы не ограничивать.",
        reply_markup=kb.as_markup()
    )


@router.message(FilterState.max_age)
async def process_filter_max_age(message: Message, state: FSMContext):
    text = message.text.strip() if message.text else ""
    if text == "-":
        max_age = None
    elif text.isdigit() and 18 <= int(text) <= 60:
        max_age = int(text)
    else:
        await message.answer("Введите число от 18 до 60 или <b>-</b> чтобы пропустить:")
        return

    data = await state.get_data()
    min_age = data.get('filter_min_age')

    if min_age and max_age and min_age > max_age:
        await message.answer("Максимальный возраст не может быть меньше минимального. Введите ещё раз:")
        return

    db.update_user_filters(message.from_user.id, min_age, max_age)
    await state.clear()

    user = db.get_user(message.from_user.id)
    kb = get_filter_keyboard(user)
    await message.answer("Фильтры сохранены!", reply_markup=kb.as_markup())


@router.callback_query(F.data == "filter_reset")
async def filter_reset(callback: CallbackQuery):
    db.update_user_filters(callback.from_user.id, None, None)
    user = db.get_user(callback.from_user.id)
    kb = get_filter_keyboard(user)
    await callback.message.answer("Фильтры сброшены!", reply_markup=kb.as_markup())
    await callback.answer()


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


@router.callback_query(F.data == "show_matches")
async def show_matches_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    matches = db.get_user_matches(user_id)

    if not matches:
        await callback.message.answer(
            "У вас пока нет матчей.\n\n"
            "Ждите — скоро кто-то вас оценит!"
        )
        await callback.answer()
        return

    from bot.handlers.matching import get_matches_list_keyboard
    matches_text = f"<b>Ваши матчи ({len(matches)}):</b>\n\n"
    for i, match in enumerate(matches[:10], 1):
        user = db.get_user(match['matched_user_id'])
        if user:
            matches_text += f"{i}. {user.get('age', '?')} лет, {user.get('city', '?')}\n"

    kb = get_matches_list_keyboard(matches)
    await callback.message.answer(matches_text, reply_markup=kb.as_markup())
    await callback.answer()


@router.callback_query(F.data == "show_profile")
async def show_profile_callback(callback: CallbackQuery):
    user = db.get_user(callback.from_user.id)
    if not user:
        await callback.answer("Анкета не найдена")
        return

    profile_text = format_profile(user)
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit_profile"),
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")
    )

    await send_profile_with_photo(
        callback.bot,
        callback.from_user.id,
        user,
        profile_text,
        kb.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data == "edit_profile")
async def edit_profile_callback(callback: CallbackQuery, state: FSMContext):
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="1. Возраст", callback_data="edit_age"))
    kb.row(InlineKeyboardButton(text="2. Город", callback_data="edit_city"))
    kb.row(InlineKeyboardButton(text="3. О себе", callback_data="edit_bio"))
    kb.row(InlineKeyboardButton(text="4. Кого показывать", callback_data="edit_pref"))
    kb.row(InlineKeyboardButton(text="5. Я ищу", callback_data="edit_looking_for"))
    kb.row(InlineKeyboardButton(text="6. Фото/видео", callback_data="edit_photo"))
    kb.row(InlineKeyboardButton(text="🔙 Назад", callback_data="show_profile"))

    await callback.message.answer(
        "<b>Что хотите изменить?</b>",
        reply_markup=kb.as_markup()
    )
    await callback.answer()


def get_gender_keyboard() -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="Парень", callback_data="gender_м"),
        InlineKeyboardButton(text="Девушка", callback_data="gender_ж")
    )
    return kb


def get_preferences_keyboard() -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="Парней", callback_data="pref_м"),
        InlineKeyboardButton(text="Девушек", callback_data="pref_ж")
    )
    kb.row(
        InlineKeyboardButton(text="Всех", callback_data="pref_все")
    )
    return kb


def get_looking_for_keyboard() -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="Все и сразу", callback_data="lookfor_all_now"))
    kb.row(InlineKeyboardButton(text="Без обязательств", callback_data="lookfor_no_strings"))
    kb.row(InlineKeyboardButton(text="Вирт", callback_data="lookfor_virt"))
    kb.row(InlineKeyboardButton(text="Все серьезно", callback_data="lookfor_serious"))
    return kb


def get_cancel_keyboard() -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="Отмена", callback_data="back_to_main"))
    return kb


def get_skip_photo_keyboard() -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="Пропустить", callback_data="skip_photo"))
    kb.row(InlineKeyboardButton(text="Отмена", callback_data="back_to_main"))
    return kb


@router.callback_query(F.data == "edit_photo")
async def edit_photo_callback(callback: CallbackQuery, state: FSMContext):
    await state.update_data(editing=True)
    await state.set_state(Registration.photo)

    kb = get_skip_photo_keyboard()
    await callback.message.answer(
        "Пришли новое фото или видео (до 15 сек):",
        reply_markup=kb.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data == "edit_age")
async def edit_age_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(EditProfile.age)
    await callback.message.answer("Введите новый возраст (18-60):")
    await callback.answer()


@router.message(EditProfile.age)
async def process_edit_age(message: Message, state: FSMContext):
    if not message.text or not message.text.isdigit() or not (18 <= int(message.text) <= 60):
        await message.answer("Введите корректный возраст (число от 18 до 60):")
        return
    db.update_user_field(message.from_user.id, 'age', int(message.text))
    await state.clear()
    await message.answer("Возраст обновлен!")
    await show_updated_profile(message.bot, message.from_user.id)


@router.callback_query(F.data == "edit_city")
async def edit_city_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(EditProfile.city)
    await callback.message.answer("Введите новый город:")
    await callback.answer()


@router.message(EditProfile.city)
async def process_edit_city(message: Message, state: FSMContext):
    if not message.text or len(message.text) < 2:
        await message.answer("Название города слишком короткое. Введите ещё раз:")
        return
    db.update_user_field(message.from_user.id, 'city', message.text.strip().title())
    await state.clear()
    await message.answer("Город обновлен!")
    await show_updated_profile(message.bot, message.from_user.id)


@router.callback_query(F.data == "edit_bio")
async def edit_bio_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(EditProfile.bio)
    await callback.message.answer(
        "Расскажите о себе:\n(минимум 3 символа или '-' чтобы убрать)"
    )
    await callback.answer()


@router.message(EditProfile.bio)
async def process_edit_bio(message: Message, state: FSMContext):
    bio_text = message.text.strip() if message.text else ""
    if bio_text != "-" and len(bio_text) < 3:
        await message.answer("Минимум 3 символа или '-' чтобы убрать:")
        return
    if bio_text == "-":
        bio_text = "Не указано"
    db.update_user_field(message.from_user.id, 'bio', bio_text)
    await state.clear()
    await message.answer("Описание обновлено!")
    await show_updated_profile(message.bot, message.from_user.id)


@router.callback_query(F.data == "edit_pref")
async def edit_pref_callback(callback: CallbackQuery, state: FSMContext):
    await state.update_data(editing_field='preferences')
    kb = get_preferences_keyboard()
    await callback.message.answer("Кого показывать?", reply_markup=kb.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("pref_"))
async def process_preferences(callback: CallbackQuery, state: FSMContext):
    pref = callback.data.split("_")[1]
    data = await state.get_data()

    if data.get('editing_field') == 'preferences':
        db.update_user_field(callback.from_user.id, 'preferences', pref)
        await state.clear()
        await callback.message.answer("Предпочтения обновлены!")
        await show_updated_profile(callback.bot, callback.from_user.id)
        await callback.answer()
        return

    await callback.answer()


@router.callback_query(F.data == "edit_looking_for")
async def edit_looking_for_callback(callback: CallbackQuery, state: FSMContext):
    await state.update_data(editing_field='looking_for')
    kb = get_looking_for_keyboard()
    await callback.message.answer("Что вы ищете?", reply_markup=kb.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("lookfor_"))
async def process_looking_for(callback: CallbackQuery, state: FSMContext):
    looking_for = callback.data.split("_", 1)[1]
    data = await state.get_data()

    if data.get('editing_field') == 'looking_for':
        db.update_user_field(callback.from_user.id, 'looking_for', looking_for)
        await state.clear()
        await callback.message.answer("Обновлено!")
        await show_updated_profile(callback.bot, callback.from_user.id)
        await callback.answer()
        return

    await callback.answer()


@router.callback_query(F.data.startswith("gender_"))
async def process_gender(callback: CallbackQuery, state: FSMContext):
    gender = callback.data.split("_")[1]
    data = await state.get_data()

    if data.get('editing_field') == 'gender':
        db.update_user_field(callback.from_user.id, 'gender', gender)
        await state.clear()
        await callback.message.answer("Пол обновлен!")
        await show_updated_profile(callback.bot, callback.from_user.id)
        await callback.answer()
        return

    await callback.answer()


@router.message(Registration.photo, F.photo)
async def process_photo(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    await state.update_data(photo_id=photo_id, media_type='photo')
    await finish_photo_edit(message.bot, message.from_user.id, state)


@router.message(Registration.photo, F.video)
async def process_video(message: Message, state: FSMContext):
    if message.video.duration > 15:
        kb = get_skip_photo_keyboard()
        await message.answer(
            "Видео должно быть не длиннее 15 секунд. Попробуйте ещё раз:",
            reply_markup=kb.as_markup()
        )
        return

    video_id = message.video.file_id
    await state.update_data(photo_id=video_id, media_type='video')
    await finish_photo_edit(message.bot, message.from_user.id, state)


@router.message(Registration.photo, F.video_note)
async def process_video_note(message: Message, state: FSMContext):
    video_note_id = message.video_note.file_id
    await state.update_data(photo_id=video_note_id, media_type='video_note')
    await finish_photo_edit(message.bot, message.from_user.id, state)


@router.callback_query(F.data == "skip_photo")
async def skip_photo(callback: CallbackQuery, state: FSMContext):
    await state.update_data(photo_id=None, media_type=None)
    await finish_photo_edit(callback.bot, callback.from_user.id, state)
    await callback.answer()


async def finish_photo_edit(bot, user_id: int, state: FSMContext):
    data = await state.get_data()
    photo_id = data.get('photo_id')
    media_type = data.get('media_type')
    db.update_user_field(user_id, 'photo_id', photo_id)
    db.update_user_field(user_id, 'media_type', media_type)
    await state.clear()
    await bot.send_message(user_id, "Фото/видео обновлено!")
    await show_updated_profile(bot, user_id)


async def show_updated_profile(bot, user_id: int):
    user = db.get_user(user_id)
    if not user:
        return
    profile_text = format_profile(user)
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit_profile"),
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")
    )
    await send_profile_with_photo(bot, user_id, user, profile_text, kb.as_markup())
