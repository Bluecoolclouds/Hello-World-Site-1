from aiogram.fsm.state import State, StatesGroup

class Registration(StatesGroup):
    age = State()
    gender = State()
    preferences = State()
    city = State()
    bio = State()
    photo = State()
