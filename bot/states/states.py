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
    name = State()
    services = State()
    prices = State()
    schedule = State()
    online_schedule = State()
    phone = State()
    breast = State()
    height = State()
    weight = State()
    clothing_size = State()
    shoe_size = State()
    intimate_grooming = State()
    min_age_restriction = State()


class FilterState(StatesGroup):
    min_age = State()
    max_age = State()


class CommentState(StatesGroup):
    text = State()


class GirlRegistration(StatesGroup):
    name = State()
    age = State()
    city = State()
    bio = State()
    photo = State()


class GirlMediaUpload(StatesGroup):
    collecting = State()


class PriceEdit(StatesGroup):
    field = State()


class ChatReply(StatesGroup):
    waiting_message = State()
