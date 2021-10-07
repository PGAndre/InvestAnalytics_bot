from aiogram.dispatcher.filters.state import StatesGroup, State


class Predict(StatesGroup):
    Predict = State()
    Check_Ticker = State()
    Set_Date = State()
    Confirm = State()
    Publish = State()

