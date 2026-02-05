from aiogram.fsm.state import State, StatesGroup

class Registration(StatesGroup):
    age = State()
    gender = State()
    preferences = State()
    looking_for = State()
    city = State()
    bio = State()
    photo = State()


class EditProfile(StatesGroup):
    age = State()
    city = State()
    bio = State()
