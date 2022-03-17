from aiogram.dispatcher.filters.state import StatesGroup, State


class Predict(StatesGroup):
    Predict = State()
    Check_Ticker = State()
    Set_Date = State()
    Set_Target = State()
    Set_Stop = State()
    Set_Risk = State()
    Confirm = State()
    Publish = State()

class Analytics(StatesGroup):
    Predict = State()
    Check_Analytic = State()
    Set_Nickname = State()
    Publish = State()

class Predict_comment(StatesGroup):
    Set_Comment = State()
    Confirm = State()
    Publish_Comment = State()

class Predict_average(StatesGroup):
    Set_Target = State()
    Set_Stop = State()
    Publish_average = State()


