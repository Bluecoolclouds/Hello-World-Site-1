from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
import os

from bot.db import Database

router = Router()
db = Database()

ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))


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
