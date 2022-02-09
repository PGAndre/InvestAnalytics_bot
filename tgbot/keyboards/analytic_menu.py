from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from tgbot.keyboards.callback_datas import analytic_callback


def main_menu_keyboard():
    keyboard = [[InlineKeyboardButton('📈 Управление прогнозами', callback_data=analytic_callback.new(action='pred'))],
                [InlineKeyboardButton('🚀 Получить доступ к ресурсам', callback_data=analytic_callback.new(action='link'))],
                [InlineKeyboardButton('👨‍💻 Информация о пользователе', callback_data=analytic_callback.new(action='myinfo'))]]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def first_menu_keyboard():
    keyboard = [[InlineKeyboardButton('📈 Создать прогноз', callback_data=analytic_callback.new(action='pred_1'))],
                [InlineKeyboardButton('🗓 Список активных прогнозов', callback_data=analytic_callback.new(action='pred_2'))],
                [InlineKeyboardButton('🗼 Список моих активных прогнозов', callback_data=analytic_callback.new(action='pred_3'))],
                [InlineKeyboardButton('Главное меню', callback_data=analytic_callback.new(action='main'))]]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def link_menu_keyboard():
    keyboard = [[InlineKeyboardButton('🚀 Получить ссылку на канал SosisochniePrognozi', callback_data=analytic_callback.new(action='link_channel'))],
                [InlineKeyboardButton('🧾 Получить ссылку на приватный чат SosisochniePrognozi', callback_data=analytic_callback.new(action='link_chat'))],
                [InlineKeyboardButton('Главное меню', callback_data=analytic_callback.new(action='main'))]]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def second_menu_keyboard():
    keyboard = [[InlineKeyboardButton('Submenu 2-1', callback_data='m2_1')],
                [InlineKeyboardButton('Submenu 2-2', callback_data='m2_2')],
                [InlineKeyboardButton('Main menu', callback_data='main')]]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def main_menu_message():
    return 'Добро пожаловать в главное меню:'


def first_menu_message():
    return 'Здесь вы можете управлять прогнозами:'

def link_menu_message():
    return 'Здесь вы можете получить доступ к доступным ресурсам:'


def second_menu_message():
    return 'Choose the submenu in second menu:'