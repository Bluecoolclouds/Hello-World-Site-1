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


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_USER_ID


@router.message(Command("admin_stats"))
async def cmd_admin_stats(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещён.")
        return
    
    stats = db.get_global_stats()
    
    stats_text = (
        "📊 Статистика бота:\n\n"
        f"👥 Всего пользователей: {stats['total_users']}\n"
        f"👤 Активных за сутки: {stats['active_today']}\n"
        f"📦 В архиве: {stats.get('archived_users', 0)}\n"
        f"❤️ Всего лайков: {stats['total_likes']}\n"
        f"💑 Всего матчей: {stats['total_matches']}\n"
        f"🚫 Забанено: {stats['banned_users']}\n\n"
        f"📈 Лайков сегодня: {stats['likes_today']}\n"
        f"💕 Матчей сегодня: {stats['matches_today']}"
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
    
    user_text = (
        f"👤 Информация о пользователе:\n\n"
        f"ID: {user['user_id']}\n"
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
        "<code>возраст,город,описание</code>\n\n"
        "Примеры:\n"
        "<code>22,астрахань,Люблю путешествия</code>\n"
        "<code>19,москва,-</code>\n\n"
        "Описание <code>-</code> = «Не указано»\n"
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
        f"<code>возраст,город,описание</code>\n\n"
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
        await message.answer("❌ Нужна подпись: <code>возраст,город,описание</code>")
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
        await message.answer("❌ Нужна подпись: <code>возраст,город,описание</code>")
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
    parts = caption.split(",", 2)
    if len(parts) < 2:
        await message.answer("❌ Неверный формат. Нужно: <code>возраст,город,описание</code>")
        return

    try:
        age = int(parts[0].strip())
    except ValueError:
        await message.answer("❌ Возраст должен быть числом.")
        return

    if age < 16 or age > 99:
        await message.answer("❌ Возраст должен быть от 16 до 99.")
        return

    city = parts[1].strip().lower()
    if not city:
        await message.answer("❌ Город не может быть пустым.")
        return

    bio = parts[2].strip() if len(parts) > 2 else "Не указано"
    if bio == "-" or not bio:
        bio = "Не указано"

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

    now = time.time()
    conn.execute("""
        INSERT OR REPLACE INTO users
        (user_id, username, age, gender, city, bio, preferences, looking_for,
         photo_id, media_type, media_ids, view_count, last_search_at, search_count_hour,
         last_hour_reset, is_banned, last_active, is_archived, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 0, 0, 0, ?, 0, ?)
    """, (fake_id, None, age, gender, city, bio, preferences, '',
          main_media["id"], main_media["type"], media_ids_json, now, now))
    conn.commit()
    conn.close()

    added += 1
    await state.update_data(added=added)

    gender_label = "Д" if gender == "ж" else "П"
    media_count = len(media_list)
    media_info = f" ({media_count} фото/видео)" if media_count > 1 else ""
    await message.answer(
        f"✅ #{added} | {gender_label}, {age}, {city}{media_info} | ID: {fake_id}"
    )
