# Пример использования клавиатур и состояний в aiogram 3.x

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from bot.keyboards.keyboards import get_main_menu, get_profile_kb, get_chat_kb
from bot.states.states import Registration

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Добро пожаловать в бот знакомств!",
        reply_markup=get_main_menu()
    )

@router.message(F.text == "🔍 Искать")
async def start_search(message: Message):
    await message.answer(
        "Вот подходящая анкета:",
        reply_markup=get_profile_kb()
    )

@router.message(Command("register"))
async def start_reg(message: Message, state: FSMContext):
    await state.set_state(Registration.age)
    await message.answer("Введите ваш возраст:")

@router.message(Registration.age)
async def process_age(message: Message, state: FSMContext):
    await state.update_data(age=message.text)
    await state.set_state(Registration.gender)
    await message.answer("Укажите ваш пол:")

@router.callback_query(F.data == "like")
async def handle_like(callback: CallbackQuery):
    await callback.message.answer("Вы поставили лайк!", reply_markup=get_chat_kb())
    await callback.answer()
