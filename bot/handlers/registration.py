import json
import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, ContentType, InputMediaPhoto, InputMediaVideo
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.states.states import Registration, EditProfile, FilterState, CommentState, GirlRegistration, PriceEdit, GirlMediaUpload
from bot.keyboards.keyboards import get_main_menu, get_male_reply_keyboard
from bot.db import Database, format_online_status

router = Router()
db = Database()

ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))

PRICE_FIELDS = {
    'home_1h': 'У меня 1 час',
    'home_2h': 'У меня 2 часа',
    'home_night': 'У меня ночь',
    'out_1h': 'Выезд 1 час',
    'out_2h': 'Выезд 2 часа',
    'out_night': 'Выезд ночь',
    'contacts_hour': 'Контактов в час',
    'prepay': 'Предоплата',
}


def parse_prices(prices_str: str) -> dict:
    if not prices_str:
        return {}
    try:
        return json.loads(prices_str)
    except (json.JSONDecodeError, TypeError):
        return {}


def format_price_table(prices: dict, for_pre: bool = False) -> str:
    if not prices:
        return "Цены не заданы"

    def val(key):
        v = prices.get(key, '')
        return str(v) if v else '-'

    lines = []
    if not for_pre:
        lines.append("<b>Цены:</b>")
    lines.append(f"         {'1 час':>8} {'2 часа':>8} {'ночь':>8}")
    lines.append(f"У меня  {val('home_1h'):>8} {val('home_2h'):>8} {val('home_night'):>8}")
    lines.append(f"Выезд   {val('out_1h'):>8} {val('out_2h'):>8} {val('out_night'):>8}")
    lines.append(f"\nКонтактов в час: {val('contacts_hour')}")
    lines.append(f"Предоплата: {val('prepay')}")

    return "\n".join(lines)


def get_prices_keyboard(prices: dict) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()

    def btn(key, label):
        v = prices.get(key, '')
        display = str(v) if v else '-'
        return InlineKeyboardButton(text=f"{label}: {display}", callback_data=f"price_set_{key}")

    kb.row(InlineKeyboardButton(text="--- У меня ---", callback_data="price_noop"))
    kb.row(btn('home_1h', '1 час'), btn('home_2h', '2 часа'), btn('home_night', 'Ночь'))
    kb.row(InlineKeyboardButton(text="--- Выезд ---", callback_data="price_noop"))
    kb.row(btn('out_1h', '1 час'), btn('out_2h', '2 часа'), btn('out_night', 'Ночь'))
    kb.row(InlineKeyboardButton(text="--- Прочее ---", callback_data="price_noop"))
    kb.row(btn('contacts_hour', 'Контактов/час'), btn('prepay', 'Предоплата'))
    kb.row(InlineKeyboardButton(text="Готово", callback_data="price_done"))
    return kb


SERVICES_CATALOG = {
    'sex': {
        'name': 'Секс',
        'items': [
            'Секс классический',
            'Секс анальный',
            'Секс групповой',
            'Услуги семейной паре',
        ]
    },
    'oral': {
        'name': 'Доп',
        'items': [
            'Минет в презервативе',
            'Минет без резинки',
            'Минет глубокий',
            'Минет в машине',
            'Горловой Минет',
            'Куннилингус',
            'Поцелуи',
            'Игрушки',
            'Окончание на грудь',
            'Окончание на лицо',
            'Окончание в рот',
            'Глотаю',
            'Сквирт',
        ]
    },
    'strip': {
        'name': 'Стриптиз',
        'items': [
            'Стриптиз профи',
            'Стриптиз не профи',
        ]
    },
    'other': {
        'name': 'Разное',
        'items': [
            'Ролевые игры',
            'Фото/видео съемка',
            'Эскорт',
            'Виртуальный секс',
        ]
    },
    'video': {
        'name': 'Видео звонок',
        'items': [
            'Секс по телефону',
        ]
    },
    'massage': {
        'name': 'Массаж',
        'items': [
            'Классический',
            'Профессиональный',
            'Расслабляющий',
            'Урологический',
            'Эротический',
            'Лингам',
            'Карсай',
            'Массажный стол',
        ]
    },
    'extreme': {
        'name': 'Экстрим',
        'items': [
            'Страпон',
        ]
    },
    'request': {
        'name': 'По запросу',
        'items': [
            'Анилингус вам',
            'Анилингус мне',
            'Золот. дождь выдача',
            'Золотой дождь прием',
            'Копро вам',
            'Фистинг анальный вам',
            'Фистинг анальный мне',
            'Фистинг классический',
            'Фингеринг',
        ]
    },
    'bdsm': {
        'name': 'Садо-мазо',
        'items': [
            'Бандаж',
            'Госпожа',
            'Игры',
            'Легкая доминация',
            'Порка',
            'Рабыня',
            'Фетиш',
            'Футфетиш',
            'Трамплинг',
            'Клизма',
            'Легкая рабыня',
            'Боллбастинг',
            'Феминизация',
            'Оборудованная студия',
        ]
    },
}


def parse_services(services_str: str) -> list:
    if not services_str:
        return []
    try:
        data = json.loads(services_str)
        if isinstance(data, list):
            return data
        return []
    except (json.JSONDecodeError, TypeError):
        return []


def format_services_list(services: list) -> str:
    if not services:
        return ""
    by_cat = {}
    for cat_id, cat in SERVICES_CATALOG.items():
        matched = [s for s in cat['items'] if s in services]
        if matched:
            by_cat[cat['name']] = matched
    if not by_cat:
        return ""
    lines = ["<b>Услуги:</b>"]
    for cat_name, items in by_cat.items():
        lines.append(f"  <i>{cat_name}:</i> {', '.join(items)}")
    return "\n".join(lines)


def get_services_categories_keyboard(services: list) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    for cat_id, cat in SERVICES_CATALOG.items():
        count = len([s for s in cat['items'] if s in services])
        total = len(cat['items'])
        label = f"{cat['name']} ({count}/{total})"
        kb.row(InlineKeyboardButton(text=label, callback_data=f"svc_cat_{cat_id}"))
    kb.row(InlineKeyboardButton(text="Готово", callback_data="back_to_main"))
    return kb


def get_services_category_keyboard(cat_id: str, services: list) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    cat = SERVICES_CATALOG.get(cat_id)
    if not cat:
        return kb
    for idx, item in enumerate(cat['items']):
        check = "+" if item in services else "-"
        kb.row(InlineKeyboardButton(text=f"{check} {item}", callback_data=f"svt:{cat_id}:{idx}"))
    kb.row(InlineKeyboardButton(text="Назад к категориям", callback_data="svc_back_cats"))
    return kb


LOOKING_FOR_OPTIONS = {
    'all_now': 'Все и сразу',
    'no_strings': 'Без обязательств',
    'virt': 'Вирт',
    'serious': 'Все серьезно'
}


def format_looking_for(looking_for: str) -> str:
    return LOOKING_FOR_OPTIONS.get(looking_for, 'Не указано')


def get_male_inline_keyboard() -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="Девушки", callback_data="start_search"),
        InlineKeyboardButton(text="Фильтры", callback_data="open_filters")
    )
    kb.row(InlineKeyboardButton(text="Оценить заново", callback_data="reset_ratings"))
    return kb


def get_female_menu_keyboard() -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="Настроить / редактировать профиль", callback_data="edit_profile"))
    kb.row(InlineKeyboardButton(text="Мои фото/видео", callback_data="edit_photo"))
    kb.row(InlineKeyboardButton(text="Услуги", callback_data="edit_services"))
    kb.row(InlineKeyboardButton(text="Цены", callback_data="edit_prices"))
    kb.row(InlineKeyboardButton(text="График / онлайн", callback_data="edit_schedule"))
    kb.row(InlineKeyboardButton(text="Кто меня отслеживает / лайкнул", callback_data="my_followers"))
    kb.row(InlineKeyboardButton(text="Статистика", callback_data="girl_stats"))
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
    kb.row(InlineKeyboardButton(text=f"Возраст: {age_text}", callback_data="filter_age"))
    kb.row(InlineKeyboardButton(text="Сбросить фильтры", callback_data="filter_reset"))
    kb.row(InlineKeyboardButton(text="Начать поиск", callback_data="start_search"))
    kb.row(InlineKeyboardButton(text="Назад", callback_data="back_to_main"))
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
    name = user.get('name', '')
    is_girl = user.get('is_girl', 0)

    lines = []
    if name:
        lines.append(f"<b>{name}</b>\n")
    lines.append(f"<b>Анкета:</b>\n")

    phone = user.get('phone', '')
    if phone and is_girl:
        lines.append(f"Телефон: {phone}")

    lines.append(f"Город: {user['city']}")
    lines.append(f"Возраст: {user['age']}")

    if is_girl:
        breast = user.get('breast', '')
        if breast:
            lines.append(f"Грудь: {breast}")
        height = user.get('height')
        if height:
            lines.append(f"Рост: {height}")
        weight = user.get('weight')
        if weight:
            lines.append(f"Вес: {weight}")
        clothing_size = user.get('clothing_size', '')
        if clothing_size:
            lines.append(f"Размер одежды: {clothing_size}")
        shoe_size = user.get('shoe_size', '')
        if shoe_size:
            lines.append(f"Размер обуви: {shoe_size}")
        intimate_grooming = user.get('intimate_grooming', '')
        if intimate_grooming:
            lines.append(f"Интимная стрижка: {intimate_grooming}")
        min_age = user.get('min_age_restriction')
        if min_age:
            lines.append(f"Не моложе: {min_age} лет")
    else:
        lines.append(f"Пол: {gender_text}")

    if bio and bio != "Не указано" and bio != "":
        lines.append(f"О себе: {bio}")

    if is_girl:
        services_list = parse_services(user.get('services', ''))
        services_text = format_services_list(services_list)
        if services_text:
            lines.append("")
            lines.append(services_text)

    prices_data = parse_prices(user.get('prices', ''))
    if prices_data:
        lines.append("")
        lines.append(format_price_table(prices_data))

    schedule = user.get('schedule', '')
    if schedule:
        lines.append(f"График: {schedule}")

    is_online = user.get('is_online', 0)
    if is_online:
        lines.append("Онлайн сейчас")
    else:
        lines.append(online_status)

    comments_count = db.get_comments_count(user['user_id'])
    if comments_count > 0:
        lines.append(f"Отзывы: {comments_count}")

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
                await bot.send_message(chat_id=chat_id, text="---", reply_markup=reply_markup, parse_mode="HTML")
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

    if db.is_girl_whitelisted(user_id) and (not user or not user.get('is_girl')):
        if user:
            db.delete_user(user_id)
        await state.set_state(GirlRegistration.name)
        await message.answer(
            "<b>Создание анкеты</b>\n\n"
            "Введите ваше имя:"
        )
        return

    if user:
        if db.is_banned(user_id):
            await message.answer("Ваш аккаунт заблокирован.")
            return

        if user.get('is_girl'):
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
            kb = get_male_inline_keyboard()
            await message.answer(
                "<b>С возвращением!</b>",
                reply_markup=get_male_reply_keyboard()
            )
            await message.answer(
                "Выберите действие:",
                reply_markup=kb.as_markup()
            )
    else:
        db.create_male_user(user_id, message.from_user.username)
        kb = get_male_inline_keyboard()
        await message.answer(
            "<b>Добро пожаловать!</b>",
            reply_markup=get_male_reply_keyboard()
        )
        await message.answer(
            "Выберите действие:",
            reply_markup=kb.as_markup()
        )


@router.callback_query(F.data == "reset_ratings")
async def reset_ratings_callback(callback: CallbackQuery, state: FSMContext):
    db.reset_ratings(callback.from_user.id)
    await callback.message.answer("Все оценки сброшены! Анкеты можно просматривать заново.")
    await callback.answer()


@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user = db.get_user(callback.from_user.id)
    if user and user.get('is_girl'):
        kb = get_female_menu_keyboard()
        await callback.message.answer("Главное меню", reply_markup=kb.as_markup())
    else:
        kb = get_male_inline_keyboard()
        await callback.message.answer("Главное меню", reply_markup=get_male_reply_keyboard())
        await callback.message.answer("Выберите действие:", reply_markup=kb.as_markup())
    await callback.answer()


@router.message(F.text == "Девушки")
async def reply_browse_girls(message: Message, state: FSMContext):
    await state.clear()
    user = db.get_user(message.from_user.id)
    if not user:
        return
    from bot.handlers.search import show_next_profile_for_message
    await show_next_profile_for_message(message, user)


@router.message(F.text == "Чаты")
async def reply_open_chats(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    user = db.get_user(user_id)
    if not user:
        return

    matches = db.get_user_matches(user_id)
    if not matches:
        await message.answer(
            "У вас пока нет чатов.\n"
            "Чтобы начать общение, найдите кого-то и получите взаимный лайк!"
        )
        return

    active_matches = [m for m in matches if not db.is_blocked(user_id, m['matched_user_id'])]
    if not active_matches:
        await message.answer("Все ваши чаты заблокированы или удалены.")
        return

    from bot.handlers.chats import get_chats_list_keyboard
    chats_text = f"<b>Ваши чаты ({len(active_matches)}):</b>\n\nВыберите чат:"
    keyboard = get_chats_list_keyboard(active_matches)
    await message.answer(chats_text, reply_markup=keyboard.as_markup())


@router.message(F.text == "Профиль")
async def reply_my_profile(message: Message, state: FSMContext):
    await state.clear()
    user = db.get_user(message.from_user.id)
    if not user:
        return

    username = user.get('username', 'Не указан')
    age = user.get('age', 25)
    city = user.get('city', 'астрахань')

    text = (
        f"<b>Ваш профиль</b>\n\n"
        f"Ник: @{username}\n"
        f"Возраст: {age}\n"
        f"Город: {city}\n"
    )
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="Назад", callback_data="back_to_main"))
    await message.answer(text, reply_markup=kb.as_markup())


@router.message(F.text == "Отслеживаемые")
async def reply_my_tracked(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    tracked = db.get_tracked_users(user_id)

    if not tracked:
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text="Листать девушек", callback_data="start_search"))
        await message.answer(
            "У вас пока нет отслеживаемых.\n\n"
            "Нажмите на анкете кнопку для отслеживания.",
            reply_markup=kb.as_markup()
        )
        return

    text = f"<b>Мои отслеживаемые ({len(tracked)}):</b>\n\n"
    kb = InlineKeyboardBuilder()
    for i, t in enumerate(tracked[:15], 1):
        name = t.get('name') or f"{t['age']} лет, {t['city']}"
        online = format_online_status(t.get('last_active'))
        kb.row(InlineKeyboardButton(
            text=f"{name} | {online}",
            callback_data=f"view_tracked_{t['tracked_user_id']}"
        ))

    kb.row(InlineKeyboardButton(text="Назад", callback_data="back_to_main"))
    await message.answer(text, reply_markup=kb.as_markup())


@router.message(F.text == "Помощь")
async def reply_show_help(message: Message, state: FSMContext):
    await state.clear()
    help_text = (
        "<b>Помощь / правила</b>\n\n"
        "1. Листайте анкеты девушек\n"
        "2. Ставьте лайки или отправляйте подарки\n"
        "3. Если девушка ответит взаимностью - будет матч\n"
        "4. Отслеживайте понравившихся девушек\n"
        "5. Оставляйте отзывы на анкетах\n\n"
        "Команды:\n"
        "/start - Главное меню\n"
        "/search - Искать анкеты\n"
        "/chats - Мои чаты\n"
        "/matches - Мои матчи\n"
    )
    await message.answer(help_text)


@router.message(GirlRegistration.name)
async def girl_reg_name(message: Message, state: FSMContext):
    name = message.text.strip() if message.text else ""
    if not name or len(name) < 2:
        await message.answer("Введите корректное имя (минимум 2 символа):")
        return
    await state.update_data(name=name)
    await state.set_state(GirlRegistration.age)
    await message.answer("Сколько вам лет?")


@router.message(GirlRegistration.age)
async def girl_reg_age(message: Message, state: FSMContext):
    try:
        age = int(message.text.strip())
    except (ValueError, AttributeError):
        await message.answer("Введите возраст числом:")
        return
    if age < 16 or age > 99:
        await message.answer("Возраст должен быть от 16 до 99:")
        return
    await state.update_data(age=age)
    await state.set_state(GirlRegistration.city)
    await message.answer("Ваш город:")


@router.message(GirlRegistration.city)
async def girl_reg_city(message: Message, state: FSMContext):
    city = message.text.strip().lower() if message.text else ""
    if not city:
        await message.answer("Введите название города:")
        return
    await state.update_data(city=city)
    await state.set_state(GirlRegistration.bio)
    await message.answer("Напишите немного о себе (или отправьте '-' чтобы пропустить):")


@router.message(GirlRegistration.bio)
async def girl_reg_bio(message: Message, state: FSMContext):
    bio = message.text.strip() if message.text else ""
    if bio == "-":
        bio = ""
    await state.update_data(bio=bio)
    await state.set_state(GirlRegistration.photo)
    await message.answer("Отправьте своё фото:")


@router.message(GirlRegistration.photo, F.photo)
async def girl_reg_photo(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    data = await state.get_data()
    user_id = message.from_user.id

    db.create_girl_user(
        user_id=user_id,
        username=message.from_user.username,
        name=data['name'],
        age=data['age'],
        city=data['city'],
        bio=data.get('bio', ''),
        photo_id=photo_id,
        media_type='photo'
    )
    db.remove_girl_whitelist(user_id)
    await state.clear()

    user = db.get_user(user_id)
    profile_text = format_profile(user)
    kb = get_female_menu_keyboard()
    await message.answer(
        f"Анкета создана!\n\n{profile_text}",
        reply_markup=kb.as_markup()
    )


@router.message(GirlRegistration.photo)
async def girl_reg_photo_invalid(message: Message, state: FSMContext):
    await message.answer("Пожалуйста, отправьте фото:")


@router.callback_query(F.data == "show_help")
async def show_help(callback: CallbackQuery):
    help_text = (
        "<b>Помощь / правила</b>\n\n"
        "1. Листайте анкеты девушек\n"
        "2. Ставьте лайки или отправляйте подарки\n"
        "3. Если девушка ответит взаимностью - будет матч\n"
        "4. Отслеживайте понравившихся девушек\n"
        "5. Оставляйте отзывы на анкетах\n\n"
        "Команды:\n"
        "/start - Главное меню\n"
        "/search - Искать анкеты\n"
        "/chats - Мои чаты\n"
        "/matches - Мои матчи\n"
    )
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="Назад", callback_data="back_to_main"))
    await callback.message.answer(help_text, reply_markup=kb.as_markup())
    await callback.answer()


@router.callback_query(F.data == "my_profile_male")
async def my_profile_male(callback: CallbackQuery):
    user = db.get_user(callback.from_user.id)
    if not user:
        await callback.answer("Профиль не найден")
        return

    username = user.get('username', 'Не указан')
    age = user.get('age', 25)
    city = user.get('city', 'астрахань')

    text = (
        f"<b>Ваш профиль</b>\n\n"
        f"Ник: @{username}\n"
        f"Возраст: {age}\n"
        f"Город: {city}\n"
    )

    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="Назад", callback_data="back_to_main"))
    await callback.message.answer(text, reply_markup=kb.as_markup())
    await callback.answer()


@router.callback_query(F.data == "open_chats")
async def open_chats_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    if not user:
        await callback.answer("Ошибка")
        return

    matches = db.get_user_matches(user_id)
    if not matches:
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text="Назад", callback_data="back_to_main"))
        await callback.message.answer(
            "У вас пока нет чатов.\n"
            "Чтобы начать общение, найдите кого-то и получите взаимный лайк!",
            reply_markup=kb.as_markup()
        )
        await callback.answer()
        return

    active_matches = [m for m in matches if not db.is_blocked(user_id, m['matched_user_id'])]
    if not active_matches:
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text="Назад", callback_data="back_to_main"))
        await callback.message.answer(
            "Все ваши чаты заблокированы или удалены.",
            reply_markup=kb.as_markup()
        )
        await callback.answer()
        return

    from bot.handlers.chats import get_chats_list_keyboard
    chats_text = f"<b>Ваши чаты ({len(active_matches)}):</b>\n\nВыберите чат:"
    kb = get_chats_list_keyboard(active_matches)
    kb.row(InlineKeyboardButton(text="Назад", callback_data="back_to_main"))
    await callback.message.answer(chats_text, reply_markup=kb.as_markup())
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
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="Назад", callback_data="back_to_main"))
    await callback.message.answer(stats_text, reply_markup=kb.as_markup())
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


# === MY TRACKED (for men) ===

@router.callback_query(F.data == "my_tracked")
async def my_tracked(callback: CallbackQuery):
    user_id = callback.from_user.id
    tracked = db.get_tracked_users(user_id)

    if not tracked:
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text="Листать девушек", callback_data="start_search"))
        kb.row(InlineKeyboardButton(text="Назад", callback_data="back_to_main"))
        await callback.message.answer(
            "У вас пока нет отслеживаемых.\n\n"
            "Нажмите на анкете кнопку для отслеживания.",
            reply_markup=kb.as_markup()
        )
        await callback.answer()
        return

    text = f"<b>Мои отслеживаемые ({len(tracked)}):</b>\n\n"
    kb = InlineKeyboardBuilder()
    for i, t in enumerate(tracked[:15], 1):
        name = t.get('name') or f"{t['age']} лет, {t['city']}"
        online = format_online_status(t.get('last_active'))
        kb.row(InlineKeyboardButton(
            text=f"{name} | {online}",
            callback_data=f"view_tracked_{t['tracked_user_id']}"
        ))

    kb.row(InlineKeyboardButton(text="Назад", callback_data="back_to_main"))
    await callback.message.answer(text, reply_markup=kb.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("view_tracked_"))
async def view_tracked_profile(callback: CallbackQuery):
    tracked_id = int(callback.data.split("_")[2])
    user = db.get_user(tracked_id)
    if not user:
        await callback.answer("Профиль не найден")
        return

    profile_text = format_profile(user)
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="Написать", url=f"tg://user?id={tracked_id}"),
        InlineKeyboardButton(text="Убрать", callback_data=f"untrack_{tracked_id}")
    )
    kb.row(InlineKeyboardButton(text="Назад", callback_data="my_tracked"))
    await send_profile_with_photo(callback.bot, callback.from_user.id, user, profile_text, kb.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("track_"))
async def track_user(callback: CallbackQuery):
    tracked_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    db.add_tracking(user_id, tracked_id)
    await callback.answer("Добавлено в отслеживаемые!")


@router.callback_query(F.data.startswith("untrack_"))
async def untrack_user(callback: CallbackQuery):
    tracked_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    db.remove_tracking(user_id, tracked_id)
    await callback.answer("Убрано из отслеживаемых")
    tracked = db.get_tracked_users(user_id)
    if not tracked:
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text="Назад", callback_data="back_to_main"))
        await callback.message.answer("Список отслеживаемых пуст.", reply_markup=kb.as_markup())
    else:
        kb = InlineKeyboardBuilder()
        for t in tracked[:15]:
            name = t.get('name') or f"{t['age']} лет, {t['city']}"
            kb.row(InlineKeyboardButton(
                text=name,
                callback_data=f"view_tracked_{t['tracked_user_id']}"
            ))
        kb.row(InlineKeyboardButton(text="Назад", callback_data="back_to_main"))
        await callback.message.answer(
            f"<b>Мои отслеживаемые ({len(tracked)}):</b>",
            reply_markup=kb.as_markup()
        )


# === COMMENTS ===

@router.callback_query(F.data.startswith("comment_"))
async def start_comment(callback: CallbackQuery, state: FSMContext):
    to_id = int(callback.data.split("_")[1])
    await state.set_state(CommentState.text)
    await state.update_data(comment_to_id=to_id)
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="Отмена", callback_data="back_to_main"))
    await callback.message.answer("Напишите ваш отзыв:", reply_markup=kb.as_markup())
    await callback.answer()


@router.message(CommentState.text)
async def process_comment(message: Message, state: FSMContext):
    text = message.text.strip() if message.text else ""
    if len(text) < 2:
        await message.answer("Отзыв слишком короткий. Минимум 2 символа:")
        return
    if len(text) > 500:
        await message.answer("Отзыв слишком длинный. Максимум 500 символов:")
        return

    data = await state.get_data()
    to_id = data.get('comment_to_id')
    db.add_comment(message.from_user.id, to_id, text)
    await state.clear()
    await message.answer("Отзыв добавлен!")


@router.callback_query(F.data.startswith("view_comments_"))
async def view_comments(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[2])
    comments = db.get_comments(user_id, limit=10)

    if not comments:
        text = "<b>Отзывы:</b>\n\nПока нет отзывов."
    else:
        text = "<b>Отзывы:</b>\n\n"
        for c in comments:
            author = f"@{c['username']}" if c.get('username') else f"ID:{c['from_user_id']}"
            text += f"  {author}: {c['text']}\n\n"

    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="Оставить отзыв", callback_data=f"comment_{user_id}"))
    kb.row(InlineKeyboardButton(text="Назад", callback_data="back_to_main"))
    await callback.message.answer(text, reply_markup=kb.as_markup())
    await callback.answer()


# === GIRL FEATURES ===

@router.callback_query(F.data == "show_matches")
async def show_matches_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    matches = db.get_user_matches(user_id)

    if not matches:
        await callback.message.answer(
            "У вас пока нет матчей.\nЖдите - скоро кто-то вас оценит!"
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
        InlineKeyboardButton(text="Редактировать", callback_data="edit_profile"),
        InlineKeyboardButton(text="Назад", callback_data="back_to_main")
    )

    await send_profile_with_photo(
        callback.bot,
        callback.from_user.id,
        user,
        profile_text,
        kb.as_markup()
    )
    await callback.answer()


def get_girl_edit_profile_keyboard(user: dict) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()

    def field_btn(label, field, callback_data):
        val = user.get(field, '') or '-'
        return InlineKeyboardButton(text=f"{label}: {val}", callback_data=callback_data)

    kb.row(field_btn("Город", "city", "edit_city"))
    kb.row(field_btn("Возраст", "age", "edit_age"))
    kb.row(field_btn("Грудь", "breast", "edit_breast"))
    kb.row(field_btn("Рост", "height", "edit_height"), field_btn("Вес", "weight", "edit_weight"))
    kb.row(field_btn("Размер одежды", "clothing_size", "edit_clothing_size"))
    kb.row(field_btn("Размер обуви", "shoe_size", "edit_shoe_size"))
    kb.row(field_btn("Интимная стрижка", "intimate_grooming", "edit_intimate_grooming"))
    min_age = user.get('min_age_restriction', 18) or 18
    kb.row(InlineKeyboardButton(text=f"Не моложе: {min_age} лет", callback_data="edit_min_age_restriction"))
    kb.row(InlineKeyboardButton(text="Имя", callback_data="edit_name"))
    kb.row(InlineKeyboardButton(text="О себе", callback_data="edit_bio"))
    phone = user.get('phone', '') or '-'
    kb.row(InlineKeyboardButton(text=f"Телефон: {phone}", callback_data="edit_phone"))
    kb.row(InlineKeyboardButton(text="Назад", callback_data="back_to_main"))
    return kb


@router.callback_query(F.data == "edit_profile")
async def edit_profile_callback(callback: CallbackQuery, state: FSMContext):
    user = db.get_user(callback.from_user.id)
    is_girl = user.get('is_girl', 0) if user else 0

    if is_girl:
        kb = get_girl_edit_profile_keyboard(user)
        await callback.message.answer(
            "<b>Редактировать профиль</b>\n\nНажмите на поле, чтобы изменить:",
            reply_markup=kb.as_markup()
        )
    else:
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text="Возраст", callback_data="edit_age"))
        kb.row(InlineKeyboardButton(text="Город", callback_data="edit_city"))
        kb.row(InlineKeyboardButton(text="О себе", callback_data="edit_bio"))
        kb.row(InlineKeyboardButton(text="Кого показывать", callback_data="edit_pref"))
        kb.row(InlineKeyboardButton(text="Я ищу", callback_data="edit_looking_for"))
        kb.row(InlineKeyboardButton(text="Фото/видео", callback_data="edit_photo"))
        kb.row(InlineKeyboardButton(text="Назад", callback_data="back_to_main"))
        await callback.message.answer(
            "<b>Что хотите изменить?</b>",
            reply_markup=kb.as_markup()
        )
    await callback.answer()


@router.callback_query(F.data == "edit_services")
async def edit_services_callback(callback: CallbackQuery, state: FSMContext):
    user = db.get_user(callback.from_user.id)
    services = parse_services(user.get('services', '')) if user else []
    count = len(services)

    kb = get_services_categories_keyboard(services)
    await callback.message.answer(
        f"<b>Услуги и цены</b>\n\nВыбрано услуг: {count}\nВыберите категорию для редактирования:",
        reply_markup=kb.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data == "edit_prices")
async def edit_prices_callback(callback: CallbackQuery, state: FSMContext):
    user = db.get_user(callback.from_user.id)
    prices = parse_prices(user.get('prices', '')) if user else {}

    table_text = format_price_table(prices, for_pre=True)
    text = f"<b>Цены</b>\n\n<pre>{table_text}</pre>\n\nНажмите на поле, чтобы изменить значение:"

    kb = get_prices_keyboard(prices)
    await callback.message.answer(text, reply_markup=kb.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("svc_cat_"))
async def svc_category_view(callback: CallbackQuery, state: FSMContext):
    cat_id = callback.data.replace("svc_cat_", "")
    if cat_id not in SERVICES_CATALOG:
        await callback.answer("Категория не найдена")
        return

    user = db.get_user(callback.from_user.id)
    services = parse_services(user.get('services', '')) if user else []
    cat = SERVICES_CATALOG[cat_id]

    kb = get_services_category_keyboard(cat_id, services)
    await callback.message.answer(
        f"<b>{cat['name']}</b>\n\nНажмите, чтобы включить/выключить:",
        reply_markup=kb.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("svt:"))
async def svc_toggle_item(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer()
        return
    _, cat_id, idx_str = parts
    if cat_id not in SERVICES_CATALOG:
        await callback.answer()
        return
    try:
        idx = int(idx_str)
    except ValueError:
        await callback.answer()
        return
    cat = SERVICES_CATALOG[cat_id]
    if idx < 0 or idx >= len(cat['items']):
        await callback.answer()
        return
    item_name = cat['items'][idx]

    user = db.get_user(callback.from_user.id)
    services = parse_services(user.get('services', '')) if user else []

    if item_name in services:
        services.remove(item_name)
    else:
        services.append(item_name)

    db.update_user_field(callback.from_user.id, 'services', json.dumps(services))

    kb = get_services_category_keyboard(cat_id, services)
    try:
        await callback.message.edit_reply_markup(reply_markup=kb.as_markup())
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data == "svc_back_cats")
async def svc_back_to_categories(callback: CallbackQuery, state: FSMContext):
    user = db.get_user(callback.from_user.id)
    services = parse_services(user.get('services', '')) if user else []
    count = len(services)

    kb = get_services_categories_keyboard(services)
    await callback.message.answer(
        f"<b>Услуги и цены</b>\n\nВыбрано услуг: {count}\nВыберите категорию для редактирования:",
        reply_markup=kb.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data == "price_noop")
async def price_noop(callback: CallbackQuery):
    await callback.answer()


@router.callback_query(F.data.startswith("price_set_"))
async def price_set_field(callback: CallbackQuery, state: FSMContext):
    field = callback.data.replace("price_set_", "")
    if field not in PRICE_FIELDS:
        await callback.answer("Неизвестное поле")
        return

    label = PRICE_FIELDS[field]
    await state.set_state(PriceEdit.field)
    await state.update_data(price_field=field)

    hint = "Введите число или текст (например: 6000, нет, неограниченно):"
    if field == 'prepay':
        hint = "Введите: да или нет"
    elif field == 'contacts_hour':
        hint = "Введите число или 'неограниченно':"

    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="Убрать значение", callback_data="price_clear_field"))
    kb.row(InlineKeyboardButton(text="Отмена", callback_data="price_cancel_edit"))
    await callback.message.answer(
        f"<b>{label}</b>\n\n{hint}",
        reply_markup=kb.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data == "price_clear_field")
async def price_clear_field(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    field = data.get('price_field')
    if not field:
        await callback.answer()
        return

    user = db.get_user(callback.from_user.id)
    prices = parse_prices(user.get('prices', '')) if user else {}
    prices.pop(field, None)
    db.update_user_field(callback.from_user.id, 'prices', json.dumps(prices))
    await state.clear()

    table_text = format_price_table(prices, for_pre=True)
    kb = get_prices_keyboard(prices)
    await callback.message.answer(
        f"<b>Услуги и цены</b>\n\n<pre>{table_text}</pre>\n\nНажмите на поле, чтобы изменить:",
        reply_markup=kb.as_markup()
    )
    await callback.answer("Значение убрано")


@router.callback_query(F.data == "price_cancel_edit")
async def price_cancel_edit(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user = db.get_user(callback.from_user.id)
    prices = parse_prices(user.get('prices', '')) if user else {}
    table_text = format_price_table(prices, for_pre=True)
    kb = get_prices_keyboard(prices)
    await callback.message.answer(
        f"<b>Услуги и цены</b>\n\n<pre>{table_text}</pre>\n\nНажмите на поле, чтобы изменить:",
        reply_markup=kb.as_markup()
    )
    await callback.answer()


@router.message(PriceEdit.field)
async def process_price_value(message: Message, state: FSMContext):
    data = await state.get_data()
    field = data.get('price_field')
    if not field:
        await state.clear()
        return

    value = message.text.strip() if message.text else ""
    if not value:
        await message.answer("Введите значение:")
        return

    if len(value) > 50:
        await message.answer("Слишком длинное значение. Максимум 50 символов:")
        return

    user = db.get_user(message.from_user.id)
    prices = parse_prices(user.get('prices', '')) if user else {}
    prices[field] = value
    db.update_user_field(message.from_user.id, 'prices', json.dumps(prices))
    await state.clear()

    table_text = format_price_table(prices, for_pre=True)
    kb = get_prices_keyboard(prices)
    await message.answer(
        f"<b>Услуги и цены</b>\n\n<pre>{table_text}</pre>\n\nНажмите на поле, чтобы изменить:",
        reply_markup=kb.as_markup()
    )


@router.callback_query(F.data == "price_done")
async def price_done(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("Цены сохранены!")
    user = db.get_user(callback.from_user.id)
    if user and user.get('is_girl'):
        kb = get_female_menu_keyboard()
        await callback.message.answer("Главное меню", reply_markup=kb.as_markup())
    await callback.answer()


@router.callback_query(F.data == "edit_schedule")
async def edit_schedule_callback(callback: CallbackQuery, state: FSMContext):
    user = db.get_user(callback.from_user.id)
    current_schedule = user.get('schedule', '') if user else ''
    is_online = user.get('is_online', 0) if user else 0

    kb = InlineKeyboardBuilder()
    online_text = "Сейчас: онлайн" if is_online else "Сейчас: оффлайн"
    kb.row(InlineKeyboardButton(
        text=f"{'Выключить онлайн' if is_online else 'Включить онлайн'}",
        callback_data="toggle_online"
    ))
    kb.row(InlineKeyboardButton(text="Изменить график", callback_data="change_schedule_text"))
    kb.row(InlineKeyboardButton(text="Назад", callback_data="back_to_main"))

    text = f"<b>График / онлайн</b>\n\n{online_text}\n"
    if current_schedule:
        text += f"График: {current_schedule}\n"

    await callback.message.answer(text, reply_markup=kb.as_markup())
    await callback.answer()


@router.callback_query(F.data == "toggle_online")
async def toggle_online(callback: CallbackQuery):
    user = db.get_user(callback.from_user.id)
    if not user:
        await callback.answer("Ошибка")
        return
    new_val = 0 if user.get('is_online', 0) else 1
    db.update_user_field(callback.from_user.id, 'is_online', new_val)
    status = "Онлайн" if new_val else "Оффлайн"
    await callback.answer(f"Статус: {status}")

    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(
        text=f"{'Выключить онлайн' if new_val else 'Включить онлайн'}",
        callback_data="toggle_online"
    ))
    kb.row(InlineKeyboardButton(text="Изменить график", callback_data="change_schedule_text"))
    kb.row(InlineKeyboardButton(text="Назад", callback_data="back_to_main"))

    await callback.message.edit_text(
        f"<b>График / онлайн</b>\n\nСейчас: {'онлайн' if new_val else 'оффлайн'}",
        reply_markup=kb.as_markup()
    )


@router.callback_query(F.data == "change_schedule_text")
async def change_schedule_text(callback: CallbackQuery, state: FSMContext):
    await state.set_state(EditProfile.schedule)
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="Отмена", callback_data="back_to_main"))
    await callback.message.answer(
        "Введите ваш график (например: Пн-Пт 10:00-22:00):\n\n"
        "Или отправьте <b>-</b> чтобы убрать.",
        reply_markup=kb.as_markup()
    )
    await callback.answer()


@router.message(EditProfile.schedule)
async def process_edit_schedule(message: Message, state: FSMContext):
    text = message.text.strip() if message.text else ""
    if text == "-":
        text = ""
    db.update_user_field(message.from_user.id, 'schedule', text)
    await state.clear()
    await message.answer("График обновлён!")
    user = db.get_user(message.from_user.id)
    if user and user.get('is_girl'):
        kb = get_female_menu_keyboard()
        await message.answer("Главное меню", reply_markup=kb.as_markup())


@router.callback_query(F.data == "my_followers")
async def my_followers(callback: CallbackQuery):
    user_id = callback.from_user.id

    followers = db.get_followers(user_id)
    likes = db.get_received_likes(user_id)

    text = "<b>Кто меня отслеживает / лайкнул</b>\n\n"

    if followers:
        text += f"<b>Отслеживающие ({len(followers)}):</b>\n"
        for f in followers[:10]:
            name = f"@{f['username']}" if f.get('username') else f"ID:{f['follower_id']}"
            text += f"  {name}, {f.get('age', '?')} лет\n"
        text += "\n"

    if likes:
        text += f"<b>Лайкнули ({len(likes)}):</b>\n"
        for l in likes[:10]:
            text += f"  {l.get('age', '?')} лет, {l.get('city', '?')}\n"
        text += "\n"

    if not followers and not likes:
        text += "Пока никто не отслеживает и не лайкнул.\n"

    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="Назад", callback_data="back_to_main"))
    await callback.message.answer(text, reply_markup=kb.as_markup())
    await callback.answer()


@router.callback_query(F.data == "girl_stats")
async def girl_stats(callback: CallbackQuery):
    user_id = callback.from_user.id
    stats = db.get_girl_stats(user_id)

    text = (
        "<b>Статистика</b>\n\n"
        f"Просмотров: {stats['views']}\n"
        f"Лайков: {stats['likes_received']}\n"
        f"Отслеживающих: {stats['followers']}\n"
        f"Отзывов: {stats['comments']}\n"
        f"Матчей: {stats['matches']}\n"
        f"Активных чатов: {stats['chats_active']}\n"
    )

    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="Назад", callback_data="back_to_main"))
    await callback.message.answer(text, reply_markup=kb.as_markup())
    await callback.answer()


# === EDIT PROFILE FIELDS ===

@router.callback_query(F.data == "edit_name")
async def edit_name_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(EditProfile.name)
    await callback.message.answer("Введите новое имя:")
    await callback.answer()


@router.message(EditProfile.name)
async def process_edit_name(message: Message, state: FSMContext):
    name = message.text.strip() if message.text else ""
    if len(name) < 2:
        await message.answer("Имя слишком короткое. Минимум 2 символа:")
        return
    db.update_user_field(message.from_user.id, 'name', name)
    await state.clear()
    await message.answer("Имя обновлено!")
    await show_updated_profile(message.bot, message.from_user.id)


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


def get_girl_media_keyboard(count: int) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    if count > 0:
        kb.row(InlineKeyboardButton(text=f"Готово ({count}/5)", callback_data="girl_media_done"))
        kb.row(InlineKeyboardButton(text="Заполнить заново", callback_data="girl_media_reset"))
    kb.row(InlineKeyboardButton(text="Отмена", callback_data="girl_media_cancel"))
    return kb


@router.callback_query(F.data == "edit_photo")
async def edit_photo_callback(callback: CallbackQuery, state: FSMContext):
    user = db.get_user(callback.from_user.id)
    if user and user.get('is_girl'):
        media_ids_raw = user.get('media_ids', '')
        existing = []
        if media_ids_raw:
            try:
                existing = json.loads(media_ids_raw)
                if not isinstance(existing, list):
                    existing = []
            except (json.JSONDecodeError, TypeError):
                existing = []
        count = len(existing)
        await state.set_state(GirlMediaUpload.collecting)
        await state.update_data(media_items=existing)
        kb = get_girl_media_keyboard(count)
        await callback.message.answer(
            f"<b>Фото/видео анкеты</b>\n\n"
            f"Загружено: {count}/5\n"
            f"Отправьте фото или видео (до 15 сек). Максимум 5 материалов.",
            reply_markup=kb.as_markup()
        )
    else:
        await state.update_data(editing=True)
        await state.set_state(Registration.photo)
        kb = get_skip_photo_keyboard()
        await callback.message.answer(
            "Пришли новое фото или видео (до 15 сек):",
            reply_markup=kb.as_markup()
        )
    await callback.answer()


@router.message(GirlMediaUpload.collecting, F.photo)
async def girl_media_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    items = data.get('media_items', [])
    if len(items) >= 5:
        await message.answer("Максимум 5 материалов. Нажмите 'Готово' или 'Заполнить заново'.")
        return
    photo_id = message.photo[-1].file_id
    items.append({"id": photo_id, "type": "photo"})
    await state.update_data(media_items=items)
    kb = get_girl_media_keyboard(len(items))
    remaining = 5 - len(items)
    if remaining > 0:
        await message.answer(
            f"Добавлено! ({len(items)}/5). Можно ещё {remaining}.",
            reply_markup=kb.as_markup()
        )
    else:
        await message.answer(
            f"Загружено 5/5 — максимум. Нажмите 'Готово' для сохранения.",
            reply_markup=kb.as_markup()
        )


@router.message(GirlMediaUpload.collecting, F.video)
async def girl_media_video(message: Message, state: FSMContext):
    if message.video.duration > 15:
        await message.answer("Видео должно быть не длиннее 15 секунд. Попробуйте ещё раз.")
        return
    data = await state.get_data()
    items = data.get('media_items', [])
    if len(items) >= 5:
        await message.answer("Максимум 5 материалов. Нажмите 'Готово' или 'Заполнить заново'.")
        return
    video_id = message.video.file_id
    items.append({"id": video_id, "type": "video"})
    await state.update_data(media_items=items)
    kb = get_girl_media_keyboard(len(items))
    remaining = 5 - len(items)
    if remaining > 0:
        await message.answer(
            f"Добавлено! ({len(items)}/5). Можно ещё {remaining}.",
            reply_markup=kb.as_markup()
        )
    else:
        await message.answer(
            f"Загружено 5/5 — максимум. Нажмите 'Готово' для сохранения.",
            reply_markup=kb.as_markup()
        )


@router.message(GirlMediaUpload.collecting, F.video_note)
async def girl_media_video_note(message: Message, state: FSMContext):
    data = await state.get_data()
    items = data.get('media_items', [])
    if len(items) >= 5:
        await message.answer("Максимум 5 материалов. Нажмите 'Готово' или 'Заполнить заново'.")
        return
    vid_id = message.video_note.file_id
    items.append({"id": vid_id, "type": "video_note"})
    await state.update_data(media_items=items)
    kb = get_girl_media_keyboard(len(items))
    remaining = 5 - len(items)
    if remaining > 0:
        await message.answer(
            f"Добавлено! ({len(items)}/5). Можно ещё {remaining}.",
            reply_markup=kb.as_markup()
        )
    else:
        await message.answer(
            f"Загружено 5/5 — максимум. Нажмите 'Готово' для сохранения.",
            reply_markup=kb.as_markup()
        )


@router.message(GirlMediaUpload.collecting)
async def girl_media_invalid(message: Message, state: FSMContext):
    data = await state.get_data()
    items = data.get('media_items', [])
    kb = get_girl_media_keyboard(len(items))
    await message.answer(
        "Отправьте фото или видео (до 15 сек).",
        reply_markup=kb.as_markup()
    )


@router.callback_query(F.data == "girl_media_done")
async def girl_media_done(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    items = data.get('media_items', [])
    if not items:
        await callback.answer("Нет загруженных материалов")
        return
    valid_items = [i for i in items if isinstance(i, dict) and 'id' in i and 'type' in i]
    db.update_user_field(callback.from_user.id, 'media_ids', json.dumps(valid_items))
    if valid_items:
        db.update_user_field(callback.from_user.id, 'photo_id', valid_items[0]['id'])
        db.update_user_field(callback.from_user.id, 'media_type', valid_items[0]['type'])
    await state.clear()
    await callback.message.answer(f"Сохранено {len(valid_items)} материал(ов)!")
    await show_updated_profile(callback.message.bot, callback.from_user.id)
    await callback.answer()


@router.callback_query(F.data == "girl_media_reset")
async def girl_media_reset(callback: CallbackQuery, state: FSMContext):
    await state.update_data(media_items=[])
    db.update_user_field(callback.from_user.id, 'media_ids', '[]')
    db.update_user_field(callback.from_user.id, 'photo_id', '')
    db.update_user_field(callback.from_user.id, 'media_type', '')
    kb = get_girl_media_keyboard(0)
    await callback.message.answer(
        "<b>Фото/видео анкеты</b>\n\n"
        "Все материалы очищены. Загружено: 0/5\n"
        "Отправьте фото или видео (до 15 сек).",
        reply_markup=kb.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data == "girl_media_cancel")
async def girl_media_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("Редактирование медиа отменено.")
    user = db.get_user(callback.from_user.id)
    if user and user.get('is_girl'):
        kb = get_female_menu_keyboard()
        await callback.message.answer("Главное меню", reply_markup=kb.as_markup())
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


@router.callback_query(F.data == "edit_phone")
async def edit_phone_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(EditProfile.phone)
    await callback.message.answer("Введите номер телефона (например: +7 967 015-32-67) и часы работы:\n\nИли '-' чтобы убрать")
    await callback.answer()


@router.message(EditProfile.phone)
async def process_edit_phone(message: Message, state: FSMContext):
    text = message.text.strip() if message.text else ""
    if text == "-":
        text = ""
    if text and len(text) > 100:
        await message.answer("Слишком длинный текст. Максимум 100 символов:")
        return
    db.update_user_field(message.from_user.id, 'phone', text)
    await state.clear()
    await message.answer("Телефон обновлен!")
    await show_girl_edit_profile(message.bot, message.from_user.id)


@router.callback_query(F.data == "edit_breast")
async def edit_breast_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(EditProfile.breast)
    await callback.message.answer("Введите размер груди (например: 3):")
    await callback.answer()


@router.message(EditProfile.breast)
async def process_edit_breast(message: Message, state: FSMContext):
    text = message.text.strip() if message.text else ""
    if not text or len(text) > 20:
        await message.answer("Введите корректное значение:")
        return
    db.update_user_field(message.from_user.id, 'breast', text)
    await state.clear()
    await message.answer("Размер груди обновлен!")
    await show_girl_edit_profile(message.bot, message.from_user.id)


@router.callback_query(F.data == "edit_height")
async def edit_height_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(EditProfile.height)
    await callback.message.answer("Введите рост в см (например: 175):")
    await callback.answer()


@router.message(EditProfile.height)
async def process_edit_height(message: Message, state: FSMContext):
    if not message.text or not message.text.strip().isdigit():
        await message.answer("Введите число (рост в см):")
        return
    val = int(message.text.strip())
    if not (100 <= val <= 250):
        await message.answer("Введите корректный рост (100-250 см):")
        return
    db.update_user_field(message.from_user.id, 'height', val)
    await state.clear()
    await message.answer("Рост обновлен!")
    await show_girl_edit_profile(message.bot, message.from_user.id)


@router.callback_query(F.data == "edit_weight")
async def edit_weight_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(EditProfile.weight)
    await callback.message.answer("Введите вес в кг (например: 58):")
    await callback.answer()


@router.message(EditProfile.weight)
async def process_edit_weight(message: Message, state: FSMContext):
    if not message.text or not message.text.strip().isdigit():
        await message.answer("Введите число (вес в кг):")
        return
    val = int(message.text.strip())
    if not (30 <= val <= 200):
        await message.answer("Введите корректный вес (30-200 кг):")
        return
    db.update_user_field(message.from_user.id, 'weight', val)
    await state.clear()
    await message.answer("Вес обновлен!")
    await show_girl_edit_profile(message.bot, message.from_user.id)


@router.callback_query(F.data == "edit_clothing_size")
async def edit_clothing_size_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(EditProfile.clothing_size)
    await callback.message.answer("Введите размер одежды (например: 42):")
    await callback.answer()


@router.message(EditProfile.clothing_size)
async def process_edit_clothing_size(message: Message, state: FSMContext):
    text = message.text.strip() if message.text else ""
    if not text or len(text) > 20:
        await message.answer("Введите корректное значение:")
        return
    db.update_user_field(message.from_user.id, 'clothing_size', text)
    await state.clear()
    await message.answer("Размер одежды обновлен!")
    await show_girl_edit_profile(message.bot, message.from_user.id)


@router.callback_query(F.data == "edit_shoe_size")
async def edit_shoe_size_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(EditProfile.shoe_size)
    await callback.message.answer("Введите размер обуви (например: 37):")
    await callback.answer()


@router.message(EditProfile.shoe_size)
async def process_edit_shoe_size(message: Message, state: FSMContext):
    text = message.text.strip() if message.text else ""
    if not text or len(text) > 20:
        await message.answer("Введите корректное значение:")
        return
    db.update_user_field(message.from_user.id, 'shoe_size', text)
    await state.clear()
    await message.answer("Размер обуви обновлен!")
    await show_girl_edit_profile(message.bot, message.from_user.id)


@router.callback_query(F.data == "edit_intimate_grooming")
async def edit_intimate_grooming_callback(callback: CallbackQuery, state: FSMContext):
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="Полная депиляция", callback_data="grooming_Полная депиляция"))
    kb.row(InlineKeyboardButton(text="Частичная депиляция", callback_data="grooming_Частичная депиляция"))
    kb.row(InlineKeyboardButton(text="Натуральная", callback_data="grooming_Натуральная"))
    kb.row(InlineKeyboardButton(text="Отмена", callback_data="edit_profile"))
    await callback.message.answer("Выберите вариант:", reply_markup=kb.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("grooming_"))
async def process_grooming(callback: CallbackQuery, state: FSMContext):
    value = callback.data.replace("grooming_", "")
    db.update_user_field(callback.from_user.id, 'intimate_grooming', value)
    await callback.message.answer("Интимная стрижка обновлена!")
    await show_girl_edit_profile(callback.bot, callback.from_user.id)
    await callback.answer()


@router.callback_query(F.data == "edit_min_age_restriction")
async def edit_min_age_restriction_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(EditProfile.min_age_restriction)
    await callback.message.answer("Введите минимальный возраст клиентов (например: 18):")
    await callback.answer()


@router.message(EditProfile.min_age_restriction)
async def process_edit_min_age_restriction(message: Message, state: FSMContext):
    if not message.text or not message.text.strip().isdigit():
        await message.answer("Введите число:")
        return
    val = int(message.text.strip())
    if not (18 <= val <= 99):
        await message.answer("Введите возраст от 18 до 99:")
        return
    db.update_user_field(message.from_user.id, 'min_age_restriction', val)
    await state.clear()
    await message.answer(f"Ограничение обновлено: не моложе {val} лет")
    await show_girl_edit_profile(message.bot, message.from_user.id)


async def show_girl_edit_profile(bot, user_id: int):
    user = db.get_user(user_id)
    if not user:
        return
    kb = get_girl_edit_profile_keyboard(user)
    await bot.send_message(
        user_id,
        "<b>Редактировать профиль</b>\n\nНажмите на поле, чтобы изменить:",
        reply_markup=kb.as_markup(),
        parse_mode="HTML"
    )


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
    await state.clear()
    await callback.message.answer("Фото не изменено.")
    await callback.answer()


async def finish_photo_edit(bot, user_id: int, state: FSMContext):
    data = await state.get_data()
    photo_id = data.get('photo_id')
    media_type = data.get('media_type', 'photo')

    if photo_id:
        db.update_user_field(user_id, 'photo_id', photo_id)
        db.update_user_field(user_id, 'media_type', media_type)

    await state.clear()
    await bot.send_message(user_id, "Фото/видео обновлено!")
    await show_updated_profile(bot, user_id)


async def show_updated_profile(bot, user_id: int):
    user = db.get_user(user_id)
    if not user:
        return

    if user.get('is_girl'):
        await show_girl_edit_profile(bot, user_id)
    else:
        kb = get_male_menu_keyboard()
        await bot.send_message(user_id, "Главное меню", reply_markup=kb.as_markup())
