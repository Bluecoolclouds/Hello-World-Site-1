from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from bot.states.states import Registration
from bot.keyboards.keyboards import get_main_menu
from bot.db import Database

router = Router()
db = Database()

@router.message(Command("cancel"))
@router.message(F.text.casefold() == "отмена")
async def cancel_handler(message: Message, state: FSMContext) -> Message:
    current_state = await state.get_state()
    if current_state is None:
        return

    await state.clear()
    await message.answer(
        "Регистрация отменена. Используйте /start, чтобы начать заново.",
        reply_markup=ReplyKeyboardRemove(),
    )

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    user = db.get_user(message.from_user.id)
    if user:
        await message.answer("Вы уже зарегистрированы!", reply_markup=get_main_menu())
        return

    await state.set_state(Registration.age)
    await message.answer("Добро пожаловать! Давайте создадим ваш профиль.\nВведите ваш возраст (18-60):")

@router.message(Registration.age)
async def process_age(message: Message, state: FSMContext):
    if not message.text.isdigit() or not (18 <= int(message.text) <= 60):
        await message.answer("Пожалуйста, введите корректный возраст (число от 18 до 60):")
        return
    
    await state.update_data(age=int(message.text))
    await state.set_state(Registration.gender)
    await message.answer("Укажите ваш пол (Мужской/Женский):")

@router.message(Registration.gender)
async def process_gender(message: Message, state: FSMContext):
    if message.text.lower() not in ["мужской", "женский"]:
        await message.answer("Пожалуйста, выберите из вариантов: Мужской или Женский")
        return
        
    await state.update_data(gender=message.text)
    await state.set_state(Registration.city)
    await message.answer("Из какого вы города?")

@router.message(Registration.city)
async def process_city(message: Message, state: FSMContext):
    if len(message.text) < 2:
        await message.answer("Название города слишком короткое. Введите еще раз:")
        return
        
    await state.update_data(city=message.text)
    await state.set_state(Registration.bio)
    await message.answer("Расскажите немного о себе (био):")

@router.message(Registration.bio)
async def process_bio(message: Message, state: FSMContext):
    if len(message.text) < 10:
        await message.answer("Био должно быть не менее 10 символов. Расскажите поподробнее:")
        return
        
    await state.update_data(bio=message.text)
    await state.set_state(Registration.preferences)
    await message.answer("Кто вас интересует? (Предпочтения):")

@router.message(Registration.preferences)
async def process_preferences(message: Message, state: FSMContext):
    await state.update_data(preferences=message.text)
    data = await state.get_data()
    
    db.save_user(message.from_user.id, data)
    await state.clear()
    
    await message.answer(
        "Регистрация успешно завершена!",
        reply_markup=get_main_menu()
    )
