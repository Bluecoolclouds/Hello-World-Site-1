import html

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext

from bot.db import Database
from bot.keyboards.keyboards import get_main_menu
from bot.states.states import ChatReply

router = Router()
db = Database()


@router.message(Command("chats"))
@router.message(F.text == "💌 Чаты")
@router.message(F.text == "Чаты")
async def cmd_chats(message: Message):
    user_id = message.from_user.id
    user = db.get_user(user_id)

    if not user:
        await message.answer("Сначала зарегистрируйтесь! /start")
        return

    is_girl = user.get('is_girl', 0)

    if is_girl:
        chats = db.get_girl_chats(user_id)
        if not chats:
            await message.answer("У вас пока нет сообщений от клиентов.")
            return

        kb = InlineKeyboardBuilder()
        for chat in chats[:20]:
            client_name = chat.get('name') or 'Аноним'
            label = f"💬 {client_name}, {chat.get('age', '?')}"
            kb.row(InlineKeyboardButton(
                text=label,
                callback_data=f"openchat_{chat['id']}"
            ))

        await message.answer(
            f"💬 Сообщения от клиентов ({len(chats)}):",
            reply_markup=kb.as_markup()
        )
    else:
        chats = db.get_client_chats(user_id)
        if not chats:
            await message.answer(
                "У вас пока нет чатов.\n\n"
                "Нажмите «Написать» на профиле девушки, чтобы начать общение."
            )
            return

        kb = InlineKeyboardBuilder()
        for chat in chats[:20]:
            girl_name = chat.get('name') or f"Девушка {chat['girl_id']}"
            online = " 🟢" if chat.get('is_online') else ""
            label = f"💬 {girl_name}{online}"
            kb.row(InlineKeyboardButton(
                text=label,
                callback_data=f"openchat_{chat['id']}"
            ))

        await message.answer(
            f"💬 Ваши чаты ({len(chats)}):",
            reply_markup=kb.as_markup()
        )


@router.callback_query(F.data.regexp(r"^openchat_\d+$"))
async def open_chat(callback: CallbackQuery):
    chat_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    chat = db.get_bot_chat(chat_id)

    if not chat:
        await callback.answer("Чат не найден")
        return

    is_client = (chat['client_id'] == user_id)
    is_girl = (chat['girl_id'] == user_id)

    if not is_client and not is_girl:
        await callback.answer("Нет доступа")
        return

    if is_client:
        other_user = db.get_user(chat['girl_id'])
        other_name = other_user.get('name', '') if other_user else 'Девушка'
        if not other_name:
            other_name = 'Девушка'
    else:
        other_user = db.get_user(chat['client_id'])
        other_name = other_user.get('name', '') if other_user else 'Аноним'
        if not other_name:
            other_name = 'Аноним'

    messages = db.get_bot_chat_messages(chat_id, limit=10)

    lines = [f"💬 Чат с <b>{other_name}</b>\n"]

    if messages:
        for msg in messages:
            if msg['sender_id'] == user_id:
                prefix = "Вы"
            else:
                prefix = other_name

            if msg.get('text'):
                lines.append(f"<b>{prefix}:</b> {html.escape(msg['text'])}")
            elif msg.get('media_type'):
                lines.append(f"<b>{prefix}:</b> [{msg['media_type']}]")
    else:
        lines.append("Сообщений пока нет")

    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(
        text="✏️ Написать",
        callback_data=f"reply_chat_{chat_id}"
    ))
    kb.row(InlineKeyboardButton(
        text="⬅️ Назад к чатам",
        callback_data="back_to_chats"
    ))

    await callback.message.answer(
        "\n".join(lines),
        reply_markup=kb.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_chats")
async def back_to_chats(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = callback.from_user.id
    user = db.get_user(user_id)

    if not user:
        await callback.answer("Профиль не найден")
        return

    is_girl = user.get('is_girl', 0)

    if is_girl:
        chats = db.get_girl_chats(user_id)
    else:
        chats = db.get_client_chats(user_id)

    if not chats:
        await callback.message.answer("Чатов пока нет.")
        await callback.answer()
        return

    kb = InlineKeyboardBuilder()
    for chat in chats[:20]:
        if is_girl:
            name = chat.get('name') or 'Аноним'
            label = f"💬 {name}, {chat.get('age', '?')}"
        else:
            name = chat.get('name') or f"Девушка {chat['girl_id']}"
            online = " 🟢" if chat.get('is_online') else ""
            label = f"💬 {name}{online}"
        kb.row(InlineKeyboardButton(
            text=label,
            callback_data=f"openchat_{chat['id']}"
        ))

    await callback.message.answer(
        f"💬 Ваши чаты ({len(chats)}):",
        reply_markup=kb.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.regexp(r"^reply_chat_\d+$"))
async def start_reply(callback: CallbackQuery, state: FSMContext):
    chat_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    chat = db.get_bot_chat(chat_id)

    if not chat:
        await callback.answer("Чат не найден")
        return

    if chat['client_id'] != user_id and chat['girl_id'] != user_id:
        await callback.answer("Нет доступа")
        return

    await state.set_state(ChatReply.waiting_message)
    await state.update_data(chat_id=chat_id)

    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_chat_reply"))

    await callback.message.answer(
        "Напишите сообщение (текст, фото или видео):",
        reply_markup=kb.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data == "cancel_chat_reply")
async def cancel_reply(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("Отправка отменена.")
    await callback.answer()


@router.message(ChatReply.waiting_message)
async def handle_chat_message(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    chat_id = data.get('chat_id')
    if not chat_id:
        await state.clear()
        return

    chat = db.get_bot_chat(chat_id)
    if not chat:
        await state.clear()
        await message.answer("Чат не найден.")
        return

    sender_id = message.from_user.id
    is_client = (chat['client_id'] == sender_id)
    is_girl_sender = (chat['girl_id'] == sender_id)

    if not is_client and not is_girl_sender:
        await state.clear()
        await message.answer("Нет доступа к этому чату.")
        return

    recipient_id = chat['girl_id'] if is_client else chat['client_id']

    raw_text = message.text or message.caption or ''
    text_content = html.escape(raw_text)
    media_type = None
    media_id = None

    if message.photo:
        media_type = 'photo'
        media_id = message.photo[-1].file_id
    elif message.video:
        media_type = 'video'
        media_id = message.video.file_id

    db.add_bot_message(chat_id, sender_id, raw_text, media_type, media_id)

    if is_client:
        sender_user = db.get_user(sender_id)
        sender_name = sender_user.get('name', '') if sender_user else ''
        if not sender_name:
            sender_name = 'Аноним'
        label = f"💬 Сообщение от клиента <b>{sender_name}</b>:\n\n"
    else:
        girl_user = db.get_user(sender_id)
        girl_name = girl_user.get('name', '') if girl_user else 'Девушка'
        if not girl_name:
            girl_name = 'Девушка'
        label = f"💬 Ответ от <b>{girl_name}</b>:\n\n"

    reply_kb = InlineKeyboardBuilder()
    reply_kb.row(InlineKeyboardButton(
        text="✏️ Ответить",
        callback_data=f"reply_chat_{chat_id}"
    ))

    try:
        if media_type == 'photo':
            await bot.send_photo(
                recipient_id,
                photo=media_id,
                caption=label + text_content,
                reply_markup=reply_kb.as_markup(),
                parse_mode="HTML"
            )
        elif media_type == 'video':
            await bot.send_video(
                recipient_id,
                video=media_id,
                caption=label + text_content,
                reply_markup=reply_kb.as_markup(),
                parse_mode="HTML"
            )
        else:
            await bot.send_message(
                recipient_id,
                label + text_content,
                reply_markup=reply_kb.as_markup(),
                parse_mode="HTML"
            )
        await message.answer("Сообщение отправлено!")
    except Exception:
        await message.answer("Не удалось доставить сообщение. Возможно, получатель заблокировал бота.")

    await state.clear()


async def start_chat_with_girl(bot: Bot, client_id: int, girl_id: int):
    chat_id = db.get_or_create_bot_chat(client_id, girl_id)
    db.add_tracking(client_id, girl_id)

    girl = db.get_user(girl_id)
    girl_name = girl.get('name', 'Девушка') if girl else 'Девушка'
    if not girl_name:
        girl_name = 'Девушка'

    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(
        text="✏️ Написать",
        callback_data=f"reply_chat_{chat_id}"
    ))

    await bot.send_message(
        client_id,
        f"💬 Чат с <b>{girl_name}</b> создан!\n\n"
        "Нажмите «Написать» чтобы отправить сообщение.",
        reply_markup=kb.as_markup(),
        parse_mode="HTML"
    )

    client = db.get_user(client_id)
    client_name = client.get('name', '') if client else ''
    if not client_name:
        client_name = 'Аноним'

    try:
        notify_kb = InlineKeyboardBuilder()
        notify_kb.row(InlineKeyboardButton(
            text="💬 Открыть чат",
            callback_data=f"openchat_{chat_id}"
        ))
        await bot.send_message(
            girl_id,
            f"💬 Новое сообщение от клиента <b>{client_name}</b>!\n\n"
            "Нажмите чтобы ответить.",
            reply_markup=notify_kb.as_markup(),
            parse_mode="HTML"
        )
    except Exception:
        pass
