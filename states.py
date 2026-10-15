from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    first_name = State()
    last_name = State()
    institute = State()
    group = State()
    confirm = State()


class Feedback(StatesGroup):
    waiting = State()


class AdminFlow(StatesGroup):
    broadcast_choose_audience = State()
    broadcast_content = State()
    dm_user_id = State()
    dm_content = State()