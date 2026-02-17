from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
import os
import time
import json
import asyncio
import sqlite3

from bot.db import Database
from bot.keyboards.keyboards import get_main_menu

_media_group_buffers: dict = {}

router = Router()
db = Database()

ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))


class AdminStates(StatesGroup):
    adding_profiles = State()
    managing_girl = State()


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_USER_ID


@router.message(Command("admin_stats"))
async def cmd_admin_stats(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещён.")
        return
    
    stats = db.get_global_stats()
    gift_stats = db.get_gifts_stats()
    
    stats_text = (
        "📊 Статистика бота:\n\n"
        f"👥 Всего пользователей: {stats['total_users']}\n"
        f"🤖 Fake-анкет: {stats.get('fake_users', 0)}\n"
        f"👤 Активных за сутки: {stats['active_today']}\n"
        f"📦 В архиве: {stats.get('archived_users', 0)}\n"
        f"❤️ Всего лайков: {stats['total_likes']}\n"
        f"💑 Всего матчей: {stats['total_matches']}\n"
        f"🚫 Забанено: {stats['banned_users']}\n\n"
        f"📈 Лайков сегодня: {stats['likes_today']}\n"
        f"💕 Матчей сегодня: {stats['matches_today']}\n\n"
        f"🎁 Подарков: {gift_stats['total_gifts']} (⭐ {gift_stats['total_stars']} звёзд)"
    )
    
    await message.answer(stats_text)


@router.message(Command("admin_ban"))
async def cmd_admin_ban(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещён.")
        return
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "❌ Использование: /admin_ban @username или user_id\n"
            "Пример: /admin_ban @user123 или /admin_ban 123456789"
        )
        return
    
    target = args[1].strip()
    
    if target.startswith("@"):
        username = target[1:]
        user = db.get_user_by_username(username)
        if not user:
            await message.answer(f"❌ Пользователь {target} не найден.")
            return
        user_id = user['user_id']
    else:
        try:
            user_id = int(target)
        except ValueError:
            await message.answer("❌ Неверный формат. Укажите @username или числовой ID.")
            return
    
    if user_id == ADMIN_USER_ID:
        await message.answer("❌ Нельзя забанить администратора.")
        return
    
    db.ban_user(user_id)
    await message.answer(f"✅ Пользователь {target} (ID: {user_id}) забанен.")


@router.message(Command("admin_unban"))
async def cmd_admin_unban(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещён.")
        return
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "❌ Использование: /admin_unban @username или user_id\n"
            "Пример: /admin_unban @user123 или /admin_unban 123456789"
        )
        return
    
    target = args[1].strip()
    
    if target.startswith("@"):
        username = target[1:]
        user = db.get_user_by_username(username)
        if not user:
            await message.answer(f"❌ Пользователь {target} не найден.")
            return
        user_id = user['user_id']
    else:
        try:
            user_id = int(target)
        except ValueError:
            await message.answer("❌ Неверный формат. Укажите @username или числовой ID.")
            return
    
    db.unban_user(user_id)
    await message.answer(f"✅ Пользователь {target} (ID: {user_id}) разбанен.")


@router.message(Command("admin_user"))
async def cmd_admin_user(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещён.")
        return
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❌ Использование: /admin_user @username или user_id")
        return
    
    target = args[1].strip()
    
    if target.startswith("@"):
        username = target[1:]
        user = db.get_user_by_username(username)
    else:
        try:
            user_id = int(target)
            user = db.get_user(user_id)
        except ValueError:
            await message.answer("❌ Неверный формат.")
            return
    
    if not user:
        await message.answer(f"❌ Пользователь {target} не найден.")
        return
    
    stats = db.get_user_stats(user['user_id'])
    banned = db.is_banned(user['user_id'])
    
    is_fake = user.get('is_fake', 0)
    fake_line = "Тип: fake\n" if is_fake else ""
    user_text = (
        f"👤 Информация о пользователе:\n\n"
        f"ID: {user['user_id']}\n"
        f"{fake_line}"
        f"Username: @{user.get('username', 'нет')}\n"
        f"Возраст: {user['age']}\n"
        f"Пол: {user['gender']}\n"
        f"Город: {user['city']}\n"
        f"Статус: {'🚫 Забанен' if banned else '✅ Активен'}\n\n"
        f"📊 Статистика:\n"
        f"Просмотров: {stats['view_count']}\n"
        f"Лайков отправлено: {stats['likes_sent']}\n"
        f"Лайков получено: {stats['likes_received']}\n"
        f"Матчей: {stats['matches_count']}"
    )
    
    await message.answer(user_text)


@router.message(Command("admin_broadcast"))
async def cmd_admin_broadcast(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещён.")
        return
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❌ Использование: /admin_broadcast Текст сообщения")
        return
    
    broadcast_text = args[1]
    users = db.get_all_active_users()
    
    sent = 0
    failed = 0
    
    for user in users:
        try:
            await message.bot.send_message(user['user_id'], f"📢 {broadcast_text}")
            sent += 1
        except Exception:
            failed += 1
    
    await message.answer(f"✅ Рассылка завершена.\nОтправлено: {sent}\nОшибок: {failed}")


@router.message(Command("admin_cleanup"))
async def cmd_admin_cleanup(message: Message):
    """Ручной запуск архивации неактивных пользователей"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещён.")
        return
    
    await message.answer("🔄 Запускаю архивацию неактивных пользователей...")
    
    archived_count = db.archive_inactive_users(days=7)
    
    await message.answer(
        f"✅ Архивация завершена!\n"
        f"📦 Архивировано пользователей: {archived_count}"
    )


@router.message(Command("admin_archive_stats"))
async def cmd_admin_archive_stats(message: Message):
    """Статистика по архивации и онлайну"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещён.")
        return
    
    stats = db.get_archive_stats()
    
    stats_text = (
        "📊 <b>Статистика активности:</b>\n\n"
        f"👥 Всего пользователей: {stats['total']}\n"
        f"✅ Активных: {stats['active']}\n"
        f"📦 В архиве: {stats['archived']}\n\n"
        f"<b>Онлайн статистика:</b>\n"
        f"🟢 Онлайн сейчас (5 мин): {stats['online_5min']}\n"
        f"🟡 Был за последний час: {stats['online_hour']}\n"
        f"🟠 Был за последние сутки: {stats['online_day']}"
    )
    
    await message.answer(stats_text)


@router.message(Command("admin_girl"))
async def cmd_admin_girl(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещён.")
        return

    args = message.text.split()
    if len(args) < 2:
        await message.answer(
            "<b>Выдать доступ девушке</b>\n\n"
            "Использование:\n"
            "<code>/admin_girl TG_ID</code>\n\n"
            "Пример:\n"
            "<code>/admin_girl 123456789</code>\n\n"
            "После этого девушка пишет боту /start и сама создаёт свою анкету.\n"
            "TG ID можно узнать через @userinfobot"
        )
        return

    try:
        girl_id = int(args[1])
    except ValueError:
        await message.answer("ID должен быть числом.")
        return

    existing = db.get_user(girl_id)
    if existing and existing.get('is_girl'):
        await message.answer(f"Пользователь {girl_id} уже зарегистрирован как девушка.")
        return

    db.add_girl_whitelist(girl_id)
    await message.answer(
        f"Доступ выдан для TG ID <code>{girl_id}</code>.\n\n"
        f"Теперь девушка пишет боту /start и заполняет свою анкету."
    )


@router.message(Command("admin_add"))
@router.message(F.text == "📥 Добавить анкеты")
async def cmd_admin_add(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещён.")
        return

    await state.set_state(AdminStates.adding_profiles)
    await state.update_data(added=0, gender="ж")

    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="👩 Девушки", callback_data="add_gender_ж"),
        InlineKeyboardButton(text="👨 Парни", callback_data="add_gender_м")
    )
    kb.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="add_done")
    )

    await message.answer(
        "📥 <b>Режим добавления анкет</b>\n\n"
        "Отправляйте фото или видео с подписью в формате:\n"
        "<code>имя, возраст, город – описание</code>\n\n"
        "Пример:\n"
        "<code>Даша, 18, Москва – inst: hoxolia</code>\n\n"
        "Пол: 👩 Девушка\n\n"
        "Нажмите кнопку чтобы сменить пол или завершить.",
        reply_markup=kb.as_markup()
    )


@router.callback_query(F.data.startswith("add_gender_"))
async def cb_add_gender(callback: CallbackQuery, state: FSMContext):
    current = await state.get_state()
    if current != AdminStates.adding_profiles.state:
        await callback.answer()
        return

    gender = callback.data.split("_")[-1]
    await state.update_data(gender=gender)
    label = "👩 Девушка" if gender == "ж" else "👨 Парень"
    await callback.message.edit_text(
        f"📥 <b>Режим добавления анкет</b>\n\n"
        f"Отправляйте фото или видео с подписью в формате:\n"
        f"<code>имя, возраст, город – описание</code>\n\n"
        f"Пол: {label}\n\n"
        f"Нажмите кнопку чтобы сменить пол или завершить.",
        reply_markup=callback.message.reply_markup
    )
    await callback.answer(f"Пол: {label}")


@router.callback_query(F.data == "add_done")
async def cb_add_done(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    added = data.get("added", 0)
    await state.clear()
    await callback.message.edit_text(f"✅ Добавление завершено!\nДобавлено анкет: {added}")
    await callback.message.answer("Главное меню", reply_markup=get_main_menu(callback.from_user.id))
    await callback.answer()


async def _handle_media(message: Message, state: FSMContext, media_id: str, media_type: str):
    caption = message.caption
    if caption:
        await state.update_data(last_caption=caption)

    user_id = message.from_user.id

    if message.media_group_id:
        group_key = f"{user_id}_{message.media_group_id}"
        if group_key not in _media_group_buffers:
            _media_group_buffers[group_key] = {
                "items": [],
                "message": message,
                "state": state,
            }
        _media_group_buffers[group_key]["items"].append({"id": media_id, "type": media_type})
        if caption:
            _media_group_buffers[group_key]["caption"] = caption

        if len(_media_group_buffers[group_key]["items"]) == 1:
            asyncio.create_task(_process_media_group(group_key))
        return

    data = await state.get_data()
    cap = caption or data.get("last_caption")
    if not cap:
        await message.answer("❌ Нужна подпись: <code>имя, возраст, город – описание</code>")
        return

    media_list = [{"id": media_id, "type": media_type}]
    await _save_profile(message, state, media_list, cap)


async def _process_media_group(group_key: str):
    await asyncio.sleep(2.0)
    buf = _media_group_buffers.pop(group_key, None)
    if not buf:
        return

    message = buf["message"]
    state = buf["state"]
    items = buf["items"]

    caption = buf.get("caption")
    if not caption:
        data = await state.get_data()
        caption = data.get("last_caption")

    if not caption:
        await message.answer("❌ Нужна подпись: <code>имя, возраст, город – описание</code>")
        return

    await _save_profile(message, state, items, caption)


@router.message(AdminStates.adding_profiles, F.photo)
async def handle_add_photo(message: Message, state: FSMContext):
    await _handle_media(message, state, message.photo[-1].file_id, "photo")


@router.message(AdminStates.adding_profiles, F.video)
async def handle_add_video(message: Message, state: FSMContext):
    await _handle_media(message, state, message.video.file_id, "video")


@router.message(AdminStates.adding_profiles, F.video_note)
async def handle_add_video_note(message: Message, state: FSMContext):
    await message.answer(
        "⚠️ Кружочки не поддерживают подписи.\n"
        "Отправьте обычное видео или фото с подписью."
    )


@router.message(AdminStates.adding_profiles)
async def handle_add_text(message: Message, state: FSMContext):
    if message.text and not message.text.startswith("/"):
        await state.update_data(last_caption=message.text)
        await message.answer(
            f"📝 Запомнил подпись: <code>{message.text}</code>\n"
            f"Теперь отправляйте фото/видео — каждое станет отдельной анкетой."
        )


async def _save_profile(message: Message, state: FSMContext, media_list: list, caption: str):
    bio = "Не указано"
    main_part = caption
    if " – " in caption:
        main_part, bio = caption.split(" – ", 1)
        bio = bio.strip() or "Не указано"
    elif " - " in caption:
        main_part, bio = caption.split(" - ", 1)
        bio = bio.strip() or "Не указано"

    parts = [p.strip() for p in main_part.split(",")]
    if len(parts) < 3:
        await message.answer(
            "❌ Неверный формат. Нужно:\n"
            "<code>имя, возраст, город – описание</code>\n"
            "Пример: <code>Даша, 18, Москва – inst: hoxolia</code>"
        )
        return

    try:
        age = int(parts[1].strip())
    except ValueError:
        await message.answer("❌ Возраст должен быть числом.")
        return

    if age < 16 or age > 99:
        await message.answer("❌ Возраст должен быть от 16 до 99.")
        return

    city = parts[2].strip().lower()
    if not city:
        await message.answer("❌ Город не может быть пустым.")
        return

    state_data = await state.get_data()
    gender = state_data.get("gender", "ж")
    added = state_data.get("added", 0)

    preferences = "м" if gender == "ж" else "ж"

    main_media = media_list[0]
    media_ids_json = json.dumps(media_list) if len(media_list) > 1 else None

    conn = sqlite3.connect(db.db_path)
    cursor = conn.execute("SELECT MAX(user_id) FROM users")
    max_id = cursor.fetchone()[0] or 0
    fake_id = max(max_id + 1, 9000000000)

    is_girl = 1 if gender == "ж" else 0
    admin_id = message.from_user.id

    now = time.time()
    conn.execute("""
        INSERT OR REPLACE INTO users
        (user_id, username, age, gender, city, bio, preferences, looking_for,
         photo_id, media_type, media_ids, is_fake, is_girl, view_count, last_search_at, search_count_hour,
         last_hour_reset, is_banned, last_active, is_archived, created_at, name, managed_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, 0, 0, 0, 0, 0, ?, 0, ?, ?, ?)
    """, (fake_id, None, age, gender, city, bio, preferences, '',
          main_media["id"], main_media["type"], media_ids_json, is_girl, now, now, parts[0].strip(), admin_id))
    conn.commit()
    conn.close()

    added += 1
    await state.update_data(added=added)

    gender_label = "Д" if gender == "ж" else "П"
    media_count = len(media_list)
    media_info = f" ({media_count} фото/видео)" if media_count > 1 else ""
    await message.answer(
        f"✅ #{added} | {gender_label}, {age}, {city}{media_info} | ID: fake_{fake_id}"
    )


@router.message(Command("girls"))
@router.message(F.text == "👩 Мои анкеты")
async def cmd_girls(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещён.")
        return

    await state.clear()
    girls = db.get_managed_girls(message.from_user.id)

    if not girls:
        await message.answer(
            "У вас нет управляемых анкет.\n\n"
            "Добавьте анкеты через /admin_add — они автоматически привяжутся к вашему аккаунту."
        )
        return

    kb = InlineKeyboardBuilder()
    for girl in girls:
        name = girl.get('name', '') or f"ID {girl['user_id']}"
        age = girl.get('age', '?')
        city = girl.get('city', '?')
        from bot.db import is_user_online
        online = " 🟢" if is_user_online(girl) else ""
        kb.row(InlineKeyboardButton(
            text=f"👩 {name}, {age}, {city}{online}",
            callback_data=f"mgirl_{girl['user_id']}"
        ))

    await message.answer(
        f"👩 <b>Ваши анкеты ({len(girls)})</b>\n\n"
        "Выберите анкету для управления:",
        reply_markup=kb.as_markup()
    )


@router.callback_query(F.data.regexp(r"^mgirl_\d+$"))
async def manage_girl_profile(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён")
        return

    girl_id = int(callback.data.split("_")[1])
    girl = db.get_user(girl_id)

    if not girl or girl.get('managed_by') != callback.from_user.id:
        await callback.answer("Анкета не найдена или не принадлежит вам")
        return

    try:
        await callback.message.delete()
    except Exception:
        pass

    await state.update_data(managing_girl_id=girl_id)

    from bot.handlers.registration import format_profile
    profile_text = format_profile(girl)

    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="Имя", callback_data=f"gedit_name_{girl_id}"),
        InlineKeyboardButton(text="Возраст", callback_data=f"gedit_age_{girl_id}"),
        InlineKeyboardButton(text="Город", callback_data=f"gedit_city_{girl_id}")
    )
    kb.row(
        InlineKeyboardButton(text="Описание", callback_data=f"gedit_bio_{girl_id}"),
        InlineKeyboardButton(text="Фото/видео", callback_data=f"gedit_photo_{girl_id}")
    )
    kb.row(
        InlineKeyboardButton(text="Услуги", callback_data=f"gedit_services_{girl_id}"),
        InlineKeyboardButton(text="Цены", callback_data=f"gedit_prices_{girl_id}")
    )
    kb.row(
        InlineKeyboardButton(text="График/онлайн", callback_data=f"gedit_schedule_{girl_id}"),
        InlineKeyboardButton(text="Параметры", callback_data=f"gedit_params_{girl_id}")
    )
    kb.row(
        InlineKeyboardButton(text="💬 Чаты этой анкеты", callback_data=f"gchats_{girl_id}")
    )
    kb.row(
        InlineKeyboardButton(text="⬅️ К списку анкет", callback_data="back_to_girls")
    )

    from bot.handlers.registration import send_profile_with_photo
    await send_profile_with_photo(
        callback.bot, callback.from_user.id, girl,
        f"<b>Управление анкетой:</b>\n\n{profile_text}",
        reply_markup=kb.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_girls")
async def back_to_girls(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        await callback.message.delete()
    except Exception:
        pass

    girls = db.get_managed_girls(callback.from_user.id)

    if not girls:
        await callback.message.answer("У вас нет управляемых анкет.")
        await callback.answer()
        return

    kb = InlineKeyboardBuilder()
    for girl in girls:
        name = girl.get('name', '') or f"ID {girl['user_id']}"
        age = girl.get('age', '?')
        city = girl.get('city', '?')
        from bot.db import is_user_online
        online = " 🟢" if is_user_online(girl) else ""
        kb.row(InlineKeyboardButton(
            text=f"👩 {name}, {age}, {city}{online}",
            callback_data=f"mgirl_{girl['user_id']}"
        ))

    await callback.message.answer(
        f"👩 <b>Ваши анкеты ({len(girls)})</b>\n\n"
        "Выберите анкету для управления:",
        reply_markup=kb.as_markup()
    )
    await callback.answer()


class GirlEditStates(StatesGroup):
    name = State()
    age = State()
    city = State()
    bio = State()
    services = State()
    prices = State()
    schedule = State()
    online_schedule = State()
    photo = State()
    breast = State()
    height = State()
    weight = State()


@router.callback_query(F.data.regexp(r"^gedit_name_\d+$"))
async def gedit_name(callback: CallbackQuery, state: FSMContext):
    girl_id = int(callback.data.split("_")[2])
    await state.set_state(GirlEditStates.name)
    await state.update_data(managing_girl_id=girl_id)
    try:
        await callback.message.delete()
    except Exception:
        pass
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="Отмена", callback_data=f"mgirl_{girl_id}"))
    await callback.message.answer("Введите новое имя для анкеты:", reply_markup=kb.as_markup())
    await callback.answer()


@router.message(GirlEditStates.name)
async def process_gedit_name(message: Message, state: FSMContext):
    data = await state.get_data()
    girl_id = data.get('managing_girl_id')
    girl = db.get_user(girl_id)
    if not girl or girl.get('managed_by') != message.from_user.id:
        await state.clear()
        await message.answer("Нет доступа.")
        return
    name = message.text.strip() if message.text else ""
    if len(name) < 2:
        await message.answer("Имя слишком короткое. Минимум 2 символа:")
        return
    db.update_user_field(girl_id, 'name', name)
    await state.clear()
    await message.answer(f"Имя анкеты обновлено: <b>{name}</b>")
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="⬅️ К анкете", callback_data=f"mgirl_{girl_id}"))
    kb.row(InlineKeyboardButton(text="⬅️ К списку", callback_data="back_to_girls"))
    await message.answer("Что дальше?", reply_markup=kb.as_markup())


@router.callback_query(F.data.regexp(r"^gedit_age_\d+$"))
async def gedit_age(callback: CallbackQuery, state: FSMContext):
    girl_id = int(callback.data.split("_")[2])
    await state.set_state(GirlEditStates.age)
    await state.update_data(managing_girl_id=girl_id)
    try:
        await callback.message.delete()
    except Exception:
        pass
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="Отмена", callback_data=f"mgirl_{girl_id}"))
    await callback.message.answer("Введите возраст:", reply_markup=kb.as_markup())
    await callback.answer()


@router.message(GirlEditStates.age)
async def process_gedit_age(message: Message, state: FSMContext):
    data = await state.get_data()
    girl_id = data.get('managing_girl_id')
    girl = db.get_user(girl_id)
    if not girl or girl.get('managed_by') != message.from_user.id:
        await state.clear()
        await message.answer("Нет доступа.")
        return
    try:
        age = int(message.text.strip())
    except (ValueError, AttributeError):
        await message.answer("Возраст должен быть числом:")
        return
    if age < 16 or age > 99:
        await message.answer("Возраст от 16 до 99:")
        return
    db.update_user_field(girl_id, 'age', age)
    await state.clear()
    await message.answer(f"Возраст обновлён: {age}")
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="⬅️ К анкете", callback_data=f"mgirl_{girl_id}"))
    await message.answer("Что дальше?", reply_markup=kb.as_markup())


@router.callback_query(F.data.regexp(r"^gedit_city_\d+$"))
async def gedit_city(callback: CallbackQuery, state: FSMContext):
    girl_id = int(callback.data.split("_")[2])
    await state.set_state(GirlEditStates.city)
    await state.update_data(managing_girl_id=girl_id)
    try:
        await callback.message.delete()
    except Exception:
        pass
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="Отмена", callback_data=f"mgirl_{girl_id}"))
    await callback.message.answer("Введите город:", reply_markup=kb.as_markup())
    await callback.answer()


@router.message(GirlEditStates.city)
async def process_gedit_city(message: Message, state: FSMContext):
    data = await state.get_data()
    girl_id = data.get('managing_girl_id')
    girl = db.get_user(girl_id)
    if not girl or girl.get('managed_by') != message.from_user.id:
        await state.clear()
        await message.answer("Нет доступа.")
        return
    city = message.text.strip() if message.text else ""
    if not city:
        await message.answer("Город не может быть пустым:")
        return
    db.update_user_field(girl_id, 'city', city)
    await state.clear()
    await message.answer(f"Город обновлён: {city}")
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="⬅️ К анкете", callback_data=f"mgirl_{girl_id}"))
    await message.answer("Что дальше?", reply_markup=kb.as_markup())


@router.callback_query(F.data.regexp(r"^gedit_bio_\d+$"))
async def gedit_bio(callback: CallbackQuery, state: FSMContext):
    girl_id = int(callback.data.split("_")[2])
    await state.set_state(GirlEditStates.bio)
    await state.update_data(managing_girl_id=girl_id)
    try:
        await callback.message.delete()
    except Exception:
        pass
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="Отмена", callback_data=f"mgirl_{girl_id}"))
    await callback.message.answer("Введите описание анкеты:", reply_markup=kb.as_markup())
    await callback.answer()


@router.message(GirlEditStates.bio)
async def process_gedit_bio(message: Message, state: FSMContext):
    data = await state.get_data()
    girl_id = data.get('managing_girl_id')
    girl = db.get_user(girl_id)
    if not girl or girl.get('managed_by') != message.from_user.id:
        await state.clear()
        await message.answer("Нет доступа.")
        return
    bio = message.text.strip() if message.text else ""
    if not bio:
        await message.answer("Описание не может быть пустым:")
        return
    db.update_user_field(girl_id, 'bio', bio)
    await state.clear()
    await message.answer("Описание обновлено!")
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="⬅️ К анкете", callback_data=f"mgirl_{girl_id}"))
    await message.answer("Что дальше?", reply_markup=kb.as_markup())


def _get_media_list(girl: dict) -> list:
    raw = girl.get('media_ids')
    if raw:
        try:
            return json.loads(raw)
        except Exception:
            pass
    photo_id = girl.get('photo_id')
    if photo_id:
        return [{"id": photo_id, "type": girl.get('media_type', 'photo')}]
    return []


def _save_media_list(girl_id: int, media_list: list):
    if media_list:
        db.update_user_field(girl_id, 'media_ids', json.dumps(media_list))
        db.update_user_field(girl_id, 'photo_id', media_list[0]["id"])
        db.update_user_field(girl_id, 'media_type', media_list[0]["type"])
    else:
        db.update_user_field(girl_id, 'media_ids', None)
        db.update_user_field(girl_id, 'photo_id', None)
        db.update_user_field(girl_id, 'media_type', None)


def _media_manage_kb(girl_id: int, count: int) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    if count < 10:
        kb.row(InlineKeyboardButton(text="Добавить фото/видео", callback_data=f"gadd_media_{girl_id}"))
    if count > 0:
        kb.row(InlineKeyboardButton(text="Удалить все", callback_data=f"gdel_media_{girl_id}"))
    kb.row(InlineKeyboardButton(text="Назад", callback_data=f"mgirl_{girl_id}"))
    return kb


@router.callback_query(F.data.regexp(r"^gedit_photo_\d+$"))
async def gedit_photo(callback: CallbackQuery, state: FSMContext):
    girl_id = int(callback.data.split("_")[2])
    girl = db.get_user(girl_id)
    if not girl or girl.get('managed_by') != callback.from_user.id:
        await callback.answer("Нет доступа")
        return
    try:
        await callback.message.delete()
    except Exception:
        pass
    media_list = _get_media_list(girl)
    count = len(media_list)
    kb = _media_manage_kb(girl_id, count)
    await callback.message.answer(
        f"Медиа: {count}/10\n\nВыберите действие:",
        reply_markup=kb.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.regexp(r"^gadd_media_\d+$"))
async def gadd_media(callback: CallbackQuery, state: FSMContext):
    girl_id = int(callback.data.split("_")[2])
    girl = db.get_user(girl_id)
    if not girl or girl.get('managed_by') != callback.from_user.id:
        await callback.answer("Нет доступа")
        return
    media_list = _get_media_list(girl)
    if len(media_list) >= 10:
        await callback.answer("Достигнут лимит 10 медиа")
        return
    await state.set_state(GirlEditStates.photo)
    await state.update_data(managing_girl_id=girl_id)
    try:
        await callback.message.delete()
    except Exception:
        pass
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="Готово", callback_data=f"gmedia_done_{girl_id}"))
    await callback.message.answer(
        f"Медиа: {len(media_list)}/10\n\n"
        "Отправьте фото или видео. Каждый файл будет добавлен к анкете.",
        reply_markup=kb.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.regexp(r"^gdel_media_\d+$"))
async def gdel_media(callback: CallbackQuery, state: FSMContext):
    girl_id = int(callback.data.split("_")[2])
    girl = db.get_user(girl_id)
    if not girl or girl.get('managed_by') != callback.from_user.id:
        await callback.answer("Нет доступа")
        return
    _save_media_list(girl_id, [])
    try:
        await callback.message.delete()
    except Exception:
        pass
    kb = _media_manage_kb(girl_id, 0)
    await callback.message.answer(
        "Все медиа удалены.\n\nМедиа: 0/10",
        reply_markup=kb.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.regexp(r"^gmedia_done_\d+$"))
async def gmedia_done(callback: CallbackQuery, state: FSMContext):
    girl_id = int(callback.data.split("_")[2])
    await state.clear()
    try:
        await callback.message.delete()
    except Exception:
        pass
    girl = db.get_user(girl_id)
    count = len(_get_media_list(girl)) if girl else 0
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="⬅️ К анкете", callback_data=f"mgirl_{girl_id}"))
    await callback.message.answer(
        f"Медиа сохранены! Всего: {count}/10",
        reply_markup=kb.as_markup()
    )
    await callback.answer()


@router.message(GirlEditStates.photo, F.photo)
async def process_gedit_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    girl_id = data.get('managing_girl_id')
    girl = db.get_user(girl_id)
    if not girl or girl.get('managed_by') != message.from_user.id:
        await state.clear()
        await message.answer("Нет доступа.")
        return
    media_list = _get_media_list(girl)
    if len(media_list) >= 10:
        await message.answer("Достигнут лимит 10 медиа. Нажмите Готово.")
        return
    media_list.append({"id": message.photo[-1].file_id, "type": "photo"})
    _save_media_list(girl_id, media_list)
    count = len(media_list)
    kb = InlineKeyboardBuilder()
    if count < 10:
        kb.row(InlineKeyboardButton(text="Добавить ещё", callback_data=f"gadd_media_{girl_id}"))
    kb.row(InlineKeyboardButton(text="Готово", callback_data=f"gmedia_done_{girl_id}"))
    await message.answer(
        f"Фото добавлено! Медиа: {count}/10",
        reply_markup=kb.as_markup()
    )


@router.message(GirlEditStates.photo, F.video)
async def process_gedit_video(message: Message, state: FSMContext):
    data = await state.get_data()
    girl_id = data.get('managing_girl_id')
    girl = db.get_user(girl_id)
    if not girl or girl.get('managed_by') != message.from_user.id:
        await state.clear()
        await message.answer("Нет доступа.")
        return
    media_list = _get_media_list(girl)
    if len(media_list) >= 10:
        await message.answer("Достигнут лимит 10 медиа. Нажмите Готово.")
        return
    media_list.append({"id": message.video.file_id, "type": "video"})
    _save_media_list(girl_id, media_list)
    count = len(media_list)
    kb = InlineKeyboardBuilder()
    if count < 10:
        kb.row(InlineKeyboardButton(text="Добавить ещё", callback_data=f"gadd_media_{girl_id}"))
    kb.row(InlineKeyboardButton(text="Готово", callback_data=f"gmedia_done_{girl_id}"))
    await message.answer(
        f"Видео добавлено! Медиа: {count}/10",
        reply_markup=kb.as_markup()
    )


@router.callback_query(F.data.regexp(r"^gedit_services_\d+$"))
async def gedit_services(callback: CallbackQuery, state: FSMContext):
    girl_id = int(callback.data.split("_")[2])
    girl = db.get_user(girl_id)
    if not girl:
        await callback.answer("Анкета не найдена")
        return

    try:
        await callback.message.delete()
    except Exception:
        pass

    await state.update_data(managing_girl_id=girl_id)

    from bot.handlers.registration import parse_services, get_services_categories_keyboard
    current = parse_services(girl.get('services', ''))
    kb = get_services_categories_keyboard(
        current,
        cat_prefix=f"gscat_{girl_id}_",
        done_callback=f"gsvc_done_{girl_id}"
    )

    await callback.message.answer(
        "<b>Редактирование услуг</b>\n\nВыберите категорию:",
        reply_markup=kb.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.regexp(r"^gscat_\d+_\w+$"))
async def handle_gsvc_category(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_", 2)
    girl_id = int(parts[1])
    cat_id = parts[2]

    girl = db.get_user(girl_id)
    if not girl:
        await callback.answer("Ошибка")
        return

    from bot.handlers.registration import parse_services, get_services_category_keyboard
    current = parse_services(girl.get('services', ''))
    kb = get_services_category_keyboard(
        cat_id, current,
        toggle_prefix=f"gsvt_{girl_id}:",
        back_callback=f"gedit_services_{girl_id}"
    )

    try:
        await callback.message.edit_text(
            "<b>Редактирование услуг</b>\n\nВыберите услуги:",
            reply_markup=kb.as_markup()
        )
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data.regexp(r"^gsvt_\d+:\w+:\d+$"))
async def handle_gsvc_toggle(callback: CallbackQuery, state: FSMContext):
    prefix_girl, rest = callback.data.split(":", 1)
    girl_id = int(prefix_girl.replace("gsvt_", ""))
    cat_id, idx_str = rest.split(":")
    idx = int(idx_str)

    from bot.handlers.registration import parse_services, get_services_category_keyboard, SERVICES_CATALOG
    girl = db.get_user(girl_id)
    current = parse_services(girl.get('services', ''))
    cat = SERVICES_CATALOG.get(cat_id)
    if cat and 0 <= idx < len(cat['items']):
        item = cat['items'][idx]
        if item in current:
            current.remove(item)
        else:
            current.append(item)
        db.update_user_field(girl_id, 'services', json.dumps(current, ensure_ascii=False))

    kb = get_services_category_keyboard(
        cat_id, current,
        toggle_prefix=f"gsvt_{girl_id}:",
        back_callback=f"gedit_services_{girl_id}"
    )
    try:
        await callback.message.edit_reply_markup(reply_markup=kb.as_markup())
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data.regexp(r"^gsvc_done_\d+$"))
async def gsvc_done(callback: CallbackQuery, state: FSMContext):
    girl_id = int(callback.data.split("_")[2])
    await callback.answer("Услуги сохранены!")
    try:
        await callback.message.delete()
    except Exception:
        pass
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="⬅️ К анкете", callback_data=f"mgirl_{girl_id}"))
    await callback.message.answer("Услуги сохранены!", reply_markup=kb.as_markup())


@router.callback_query(F.data.regexp(r"^gedit_prices_\d+$"))
async def gedit_prices(callback: CallbackQuery, state: FSMContext):
    girl_id = int(callback.data.split("_")[2])
    girl = db.get_user(girl_id)
    if not girl:
        await callback.answer("Анкета не найдена")
        return

    try:
        await callback.message.delete()
    except Exception:
        pass

    await state.update_data(managing_girl_id=girl_id)

    from bot.handlers.registration import parse_prices, get_prices_keyboard
    prices = parse_prices(girl.get('prices', ''))
    kb = get_prices_keyboard(prices, prefix=f"gprc_{girl_id}_", done_callback=f"gprc_done_{girl_id}")

    await callback.message.answer(
        "<b>Редактирование цен</b>\n\nВыберите что изменить:",
        reply_markup=kb.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.regexp(r"^gprc_done_\d+$"))
async def gprc_done(callback: CallbackQuery, state: FSMContext):
    girl_id = int(callback.data.split("_")[2])
    await callback.answer("Цены сохранены!")
    try:
        await callback.message.delete()
    except Exception:
        pass
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="⬅️ К анкете", callback_data=f"mgirl_{girl_id}"))
    await callback.message.answer("Цены сохранены!", reply_markup=kb.as_markup())


@router.callback_query(F.data.regexp(r"^gprc_\d+_\w+$"))
async def handle_gprc(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_", 2)
    girl_id = int(parts[1])
    price_key = parts[2]

    PRICE_LABELS = {
        'home_1h': 'У меня — 1 час', 'home_2h': 'У меня — 2 часа', 'home_night': 'У меня — ночь',
        'out_1h': 'Выезд — 1 час', 'out_2h': 'Выезд — 2 часа', 'out_night': 'Выезд — ночь',
        'contacts_hour': 'Контактов/час', 'prepay': 'Предоплата'
    }

    await state.set_state(GirlEditStates.prices)
    await state.update_data(managing_girl_id=girl_id, price_field=price_key)

    label = PRICE_LABELS.get(price_key, price_key)
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="Отмена", callback_data=f"gedit_prices_{girl_id}"))
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(
        f"Введите цену для <b>{label}</b>:\n\nОтправьте <b>-</b> чтобы убрать.",
        reply_markup=kb.as_markup()
    )
    await callback.answer()


@router.message(GirlEditStates.prices)
async def process_gprc(message: Message, state: FSMContext):
    data = await state.get_data()
    girl_id = data.get('managing_girl_id')
    price_field = data.get('price_field')

    from bot.handlers.registration import parse_prices
    girl = db.get_user(girl_id)
    if not girl or girl.get('managed_by') != message.from_user.id:
        await state.clear()
        await message.answer("Нет доступа.")
        return
    prices = parse_prices(girl.get('prices', ''))

    text = message.text.strip() if message.text else ""
    if text == "-":
        prices.pop(price_field, None)
    else:
        prices[price_field] = text

    db.update_user_field(girl_id, 'prices', json.dumps(prices))
    await state.clear()
    await message.answer("Цена обновлена!")

    from bot.handlers.registration import get_prices_keyboard
    kb = get_prices_keyboard(prices, prefix=f"gprc_{girl_id}_", done_callback=f"gprc_done_{girl_id}")
    await message.answer(
        "<b>Редактирование цен</b>\n\nВыберите что изменить:",
        reply_markup=kb.as_markup()
    )


@router.callback_query(F.data.regexp(r"^gedit_schedule_\d+$"))
async def gedit_schedule(callback: CallbackQuery, state: FSMContext):
    girl_id = int(callback.data.split("_")[2])
    girl = db.get_user(girl_id)
    if not girl:
        await callback.answer("Анкета не найдена")
        return

    try:
        await callback.message.delete()
    except Exception:
        pass

    await state.update_data(managing_girl_id=girl_id)

    from bot.db import is_user_online
    is_online_manual = girl.get('is_online', 0)
    online_schedule_val = girl.get('online_schedule', '')
    actually_online = is_user_online(girl)

    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(
        text=f"{'Выключить' if is_online_manual else 'Включить'} онлайн (вручную)",
        callback_data=f"gtoggle_{girl_id}"
    ))
    kb.row(InlineKeyboardButton(
        text=f"{'Изменить' if online_schedule_val else 'Настроить'} авто-онлайн",
        callback_data=f"gauto_{girl_id}"
    ))
    if online_schedule_val:
        kb.row(InlineKeyboardButton(text="Убрать авто-онлайн", callback_data=f"gclearauto_{girl_id}"))
    kb.row(InlineKeyboardButton(
        text="Изменить график работы",
        callback_data=f"gsched_{girl_id}"
    ))
    kb.row(InlineKeyboardButton(text="⬅️ К анкете", callback_data=f"mgirl_{girl_id}"))

    status_icon = "🟢" if actually_online else "🔴"
    text = f"<b>График / онлайн ({girl.get('name', '')})</b>\n\n{status_icon} Сейчас: {'онлайн' if actually_online else 'оффлайн'}\n"
    if is_online_manual:
        text += "Ручной режим: включён\n"
    if online_schedule_val:
        text += f"Авто-онлайн: {online_schedule_val} (МСК)\n"
    schedule = girl.get('schedule', '')
    if schedule:
        text += f"График работы: {schedule}\n"

    await callback.message.answer(text, reply_markup=kb.as_markup())
    await callback.answer()


@router.callback_query(F.data.regexp(r"^gtoggle_\d+$"))
async def gtoggle_online(callback: CallbackQuery):
    girl_id = int(callback.data.split("_")[1])
    girl = db.get_user(girl_id)
    if not girl:
        await callback.answer("Ошибка")
        return
    new_val = 0 if girl.get('is_online', 0) else 1
    db.update_user_field(girl_id, 'is_online', new_val)
    status = "Онлайн" if new_val else "Оффлайн"
    await callback.answer(f"{girl.get('name', '')}: {status}")

    from bot.db import is_user_online, check_online_by_schedule
    online_schedule_val = girl.get('online_schedule', '')
    actually_online = new_val or check_online_by_schedule(online_schedule_val)

    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(
        text=f"{'Выключить' if new_val else 'Включить'} онлайн (вручную)",
        callback_data=f"gtoggle_{girl_id}"
    ))
    kb.row(InlineKeyboardButton(
        text=f"{'Изменить' if online_schedule_val else 'Настроить'} авто-онлайн",
        callback_data=f"gauto_{girl_id}"
    ))
    if online_schedule_val:
        kb.row(InlineKeyboardButton(text="Убрать авто-онлайн", callback_data=f"gclearauto_{girl_id}"))
    kb.row(InlineKeyboardButton(text="Изменить график работы", callback_data=f"gsched_{girl_id}"))
    kb.row(InlineKeyboardButton(text="⬅️ К анкете", callback_data=f"mgirl_{girl_id}"))

    status_icon = "🟢" if actually_online else "🔴"
    text = f"<b>График / онлайн ({girl.get('name', '')})</b>\n\n{status_icon} Сейчас: {'онлайн' if actually_online else 'оффлайн'}\n"
    if new_val:
        text += "Ручной режим: включён\n"
    if online_schedule_val:
        text += f"Авто-онлайн: {online_schedule_val} (МСК)\n"

    await callback.message.edit_text(text, reply_markup=kb.as_markup())


@router.callback_query(F.data.regexp(r"^gauto_\d+$"))
async def gauto_schedule(callback: CallbackQuery, state: FSMContext):
    girl_id = int(callback.data.split("_")[1])
    await state.set_state(GirlEditStates.online_schedule)
    await state.update_data(managing_girl_id=girl_id)
    try:
        await callback.message.delete()
    except Exception:
        pass
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="Отмена", callback_data=f"gedit_schedule_{girl_id}"))
    await callback.message.answer(
        "<b>Настройка авто-онлайн</b>\n\n"
        "Введите время в формате <b>ЧЧ:ММ-ЧЧ:ММ</b> (МСК)\n\n"
        "Примеры:\n"
        "• <code>00:00-06:00</code>\n"
        "• <code>22:00-06:00</code>",
        reply_markup=kb.as_markup()
    )
    await callback.answer()


@router.message(GirlEditStates.online_schedule)
async def process_gauto(message: Message, state: FSMContext):
    import re
    data = await state.get_data()
    girl_id = data.get('managing_girl_id')
    girl = db.get_user(girl_id)
    if not girl or girl.get('managed_by') != message.from_user.id:
        await state.clear()
        await message.answer("Нет доступа.")
        return
    text = message.text.strip() if message.text else ""
    match = re.match(r'^(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})$', text)
    if not match:
        await message.answer("Неверный формат. Введите <b>ЧЧ:ММ-ЧЧ:ММ</b>")
        return
    h1, m1, h2, m2 = int(match.group(1)), int(match.group(2)), int(match.group(3)), int(match.group(4))
    if h1 > 23 or m1 > 59 or h2 > 23 or m2 > 59:
        await message.answer("Некорректное время.")
        return
    schedule_str = f"{h1:02d}:{m1:02d}-{h2:02d}:{m2:02d}"
    db.update_user_field(girl_id, 'online_schedule', schedule_str)
    await state.clear()
    girl = db.get_user(girl_id)
    name = girl.get('name', '') if girl else ''
    await message.answer(f"Авто-онлайн для <b>{name}</b>: {schedule_str} (МСК)")
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="⬅️ К анкете", callback_data=f"mgirl_{girl_id}"))
    await message.answer("Что дальше?", reply_markup=kb.as_markup())


@router.callback_query(F.data.regexp(r"^gclearauto_\d+$"))
async def gclearauto(callback: CallbackQuery):
    girl_id = int(callback.data.split("_")[1])
    db.update_user_field(girl_id, 'online_schedule', '')
    await callback.answer("Авто-онлайн отключён")
    try:
        await callback.message.delete()
    except Exception:
        pass
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="⬅️ К анкете", callback_data=f"mgirl_{girl_id}"))
    await callback.message.answer("Авто-онлайн отключён.", reply_markup=kb.as_markup())


@router.callback_query(F.data.regexp(r"^gsched_\d+$"))
async def gsched(callback: CallbackQuery, state: FSMContext):
    girl_id = int(callback.data.split("_")[1])
    await state.set_state(GirlEditStates.schedule)
    await state.update_data(managing_girl_id=girl_id)
    try:
        await callback.message.delete()
    except Exception:
        pass
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="Отмена", callback_data=f"gedit_schedule_{girl_id}"))
    await callback.message.answer(
        "Введите график работы (например: Пн-Пт 10:00-22:00):\n\n"
        "Отправьте <b>-</b> чтобы убрать.",
        reply_markup=kb.as_markup()
    )
    await callback.answer()


@router.message(GirlEditStates.schedule)
async def process_gsched(message: Message, state: FSMContext):
    data = await state.get_data()
    girl_id = data.get('managing_girl_id')
    girl = db.get_user(girl_id)
    if not girl or girl.get('managed_by') != message.from_user.id:
        await state.clear()
        await message.answer("Нет доступа.")
        return
    text = message.text.strip() if message.text else ""
    if text == "-":
        text = ""
    db.update_user_field(girl_id, 'schedule', text)
    await state.clear()
    await message.answer("График обновлён!")
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="⬅️ К анкете", callback_data=f"mgirl_{girl_id}"))
    await message.answer("Что дальше?", reply_markup=kb.as_markup())


@router.callback_query(F.data.regexp(r"^gedit_params_\d+$"))
async def gedit_params(callback: CallbackQuery, state: FSMContext):
    girl_id = int(callback.data.split("_")[2])
    girl = db.get_user(girl_id)
    if not girl:
        await callback.answer("Анкета не найдена")
        return
    try:
        await callback.message.delete()
    except Exception:
        pass
    await state.update_data(managing_girl_id=girl_id)
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="Грудь", callback_data=f"gparam_breast_{girl_id}"),
        InlineKeyboardButton(text="Рост", callback_data=f"gparam_height_{girl_id}")
    )
    kb.row(
        InlineKeyboardButton(text="Вес", callback_data=f"gparam_weight_{girl_id}")
    )
    kb.row(InlineKeyboardButton(text="⬅️ К анкете", callback_data=f"mgirl_{girl_id}"))

    text = "<b>Параметры</b>\n\n"
    text += f"Грудь: {girl.get('breast', '-') or '-'}\n"
    text += f"Рост: {girl.get('height', '-') or '-'}\n"
    text += f"Вес: {girl.get('weight', '-') or '-'}\n"

    await callback.message.answer(text, reply_markup=kb.as_markup())
    await callback.answer()


@router.callback_query(F.data.regexp(r"^gparam_(breast|height|weight)_\d+$"))
async def gparam_edit(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    field = parts[1]
    girl_id = int(parts[2])

    field_map = {'breast': GirlEditStates.breast, 'height': GirlEditStates.height, 'weight': GirlEditStates.weight}
    label_map = {'breast': 'грудь', 'height': 'рост (см)', 'weight': 'вес (кг)'}

    await state.set_state(field_map[field])
    await state.update_data(managing_girl_id=girl_id, param_field=field)
    try:
        await callback.message.delete()
    except Exception:
        pass
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="Отмена", callback_data=f"gedit_params_{girl_id}"))
    await callback.message.answer(
        f"Введите {label_map[field]}:\n\nОтправьте <b>-</b> чтобы убрать.",
        reply_markup=kb.as_markup()
    )
    await callback.answer()


@router.message(GirlEditStates.breast)
@router.message(GirlEditStates.height)
@router.message(GirlEditStates.weight)
async def process_gparam(message: Message, state: FSMContext):
    data = await state.get_data()
    girl_id = data.get('managing_girl_id')
    field = data.get('param_field')
    girl = db.get_user(girl_id)
    if not girl or girl.get('managed_by') != message.from_user.id:
        await state.clear()
        await message.answer("Нет доступа.")
        return

    text = message.text.strip() if message.text else ""
    if text == "-":
        text = None

    if field in ('height', 'weight') and text:
        try:
            int(text)
        except ValueError:
            await message.answer("Введите число:")
            return

    db.update_user_field(girl_id, field, text)
    await state.clear()
    await message.answer("Параметр обновлён!")
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="⬅️ К параметрам", callback_data=f"gedit_params_{girl_id}"))
    kb.row(InlineKeyboardButton(text="⬅️ К анкете", callback_data=f"mgirl_{girl_id}"))
    await message.answer("Что дальше?", reply_markup=kb.as_markup())


@router.callback_query(F.data.regexp(r"^gchats_\d+$"))
async def gchats(callback: CallbackQuery, state: FSMContext):
    girl_id = int(callback.data.split("_")[1])
    girl = db.get_user(girl_id)
    if not girl:
        await callback.answer("Анкета не найдена")
        return
    try:
        await callback.message.delete()
    except Exception:
        pass

    chats = db.get_girl_chats(girl_id)
    girl_name = girl.get('name', '') or f"ID {girl_id}"

    if not chats:
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text="⬅️ К анкете", callback_data=f"mgirl_{girl_id}"))
        await callback.message.answer(
            f"У анкеты <b>{girl_name}</b> пока нет чатов.",
            reply_markup=kb.as_markup()
        )
        await callback.answer()
        return

    kb = InlineKeyboardBuilder()
    for chat in chats[:20]:
        client_name = chat.get('name') or 'Аноним'
        label = f"💬 {client_name}, {chat.get('age', '?')}"
        kb.row(InlineKeyboardButton(
            text=label,
            callback_data=f"openchat_{chat['id']}"
        ))
    kb.row(InlineKeyboardButton(text="⬅️ К анкете", callback_data=f"mgirl_{girl_id}"))

    await callback.message.answer(
        f"💬 Чаты анкеты <b>{girl_name}</b> ({len(chats)}):",
        reply_markup=kb.as_markup()
    )
    await callback.answer()
