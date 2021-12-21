from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

cancel_back_markup = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="назад"),
            KeyboardButton(text="отменить")
        ]
    ],
    resize_keyboard=True
)
publish = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="опубликовать")
        ]
    ],
    resize_keyboard=True
)

confirm = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="назад"),
            KeyboardButton(text="отменить")
        ],
        [
            KeyboardButton(text="опубликовать")
        ]
    ],
    resize_keyboard=True
)

confirm_no_back = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="отменить")
        ],
        [
            KeyboardButton(text="опубликовать")
        ]
    ],
    resize_keyboard=True
)

cancel = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="отменить")
        ]
    ],
    resize_keyboard=True
)
