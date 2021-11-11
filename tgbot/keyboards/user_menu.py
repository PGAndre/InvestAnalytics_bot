from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from tgbot.keyboards.callback_datas import user_callback


def main_menu_keyboard():
    keyboard = [[InlineKeyboardButton('Управление Подпиской', callback_data=user_callback.new(action='sub'))],
                [InlineKeyboardButton('Получить ссылку на канал', callback_data=user_callback.new(action='link'))],
                [InlineKeyboardButton('Информация о прогнозах', callback_data=user_callback.new(action='pred'))],
                [InlineKeyboardButton('Информация о пользователе', callback_data=user_callback.new(action='myinfo'))]]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def first_menu_keyboard():
    keyboard = [[InlineKeyboardButton('Информация о подписке', callback_data=user_callback.new(action='sub_1'))],
                [InlineKeyboardButton('Оформить\Продлить подписку', callback_data=user_callback.new(action='sub_2'))],
                [InlineKeyboardButton('Main menu', callback_data=user_callback.new(action='main'))]]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def second_menu_keyboard():
    keyboard = [[InlineKeyboardButton('Submenu 2-1', callback_data='m2_1')],
                [InlineKeyboardButton('Submenu 2-2', callback_data='m2_2')],
                [InlineKeyboardButton('Main menu', callback_data='main')]]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def main_menu_message():
    return 'Добро пожаловать в главное меню:'


def first_menu_message():
    return 'Здесь вы можете управлять своей подпиской на канал:'


def second_menu_message():
    return 'Choose the submenu in second menu:'