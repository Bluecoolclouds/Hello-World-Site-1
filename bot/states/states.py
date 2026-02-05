from aiogram.fsm.state import State, StatesGroup

class Registration(StatesGroup):
    age = State()
    gender = State()
    city = State()
    bio = State()
    preferences = State()
