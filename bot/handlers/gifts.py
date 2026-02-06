import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, PreCheckoutQuery, Message, LabeledPrice, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.db import Database

router = Router()
db = Database()
logger = logging.getLogger(__name__)

GIFT_PRICE_STARS = 1


@router.callback_query(F.data.regexp(r"^gift_\d+$"))
async def handle_gift(callback: CallbackQuery):
    to_id = int(callback.data.split("_")[1])
    from_id = callback.from_user.id

    to_user = db.get_user(to_id)
    if not to_user:
        await callback.answer("Профиль не найден", show_alert=True)
        return

    await callback.answer()

    gender_emoji = "👨" if to_user.get('gender') == 'м' else "👩"
    await callback.bot.send_invoice(
        chat_id=from_id,
        title="Подарок",
        description=f"Отправьте подарок и сразу получите контакт!\n{gender_emoji} {to_user['age']} лет, {to_user['city']}",
        payload=f"gift_{from_id}_{to_id}",
        currency="XTR",
        prices=[LabeledPrice(label="Подарок", amount=GIFT_PRICE_STARS)],
        provider_token="",
    )


@router.pre_checkout_query(F.invoice_payload.startswith("gift_"))
async def process_gift_pre_checkout(query: PreCheckoutQuery):
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def process_gift_payment(message: Message):
    payment = message.successful_payment
    payload = payment.invoice_payload

    if not payload.startswith("gift_"):
        return

    parts = payload.split("_")
    from_id = int(parts[1])
    to_id = int(parts[2])

    db.save_gift(from_id, to_id, payment.total_amount, payment.telegram_payment_charge_id)
    db.add_like(from_id, to_id)

    to_user = db.get_user(to_id)
    is_fake = to_user.get('is_fake', 0) == 1 if to_user else False

    if to_user:
        gender_emoji = "👨" if to_user.get('gender') == 'м' else "👩"
        bio = to_user.get('bio', '')

        if is_fake:
            await message.answer(
                f"🎁 Подарок отправлен!\n\n"
                f"Этот пользователь закрыл возможность моментального контакта "
                f"и оставил оценивание подарков.\n\n"
                f"Скоро она оценит ваш подарок — "
                f"он прилетит ей вне очереди!"
            )
        else:
            kb = InlineKeyboardBuilder()
            kb.row(
                InlineKeyboardButton(text="💬 Написать", url=f"tg://user?id={to_id}")
            )
            await message.answer(
                f"🎁 Подарок отправлен! Вот контакт:\n\n"
                f"{gender_emoji} {to_user['age']} лет, {to_user['city']}\n\n"
                f"Нажмите кнопку ниже, чтобы написать!",
                reply_markup=kb.as_markup()
            )
    else:
        await message.answer(
            "🎁 Подарок отправлен!",
        )

    if not is_fake:
        try:
            await message.bot.send_message(
                to_id,
                "🎁 Вам отправили подарок! Кто-то очень хочет с вами познакомиться.",
            )
        except Exception:
            pass
