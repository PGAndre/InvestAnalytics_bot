import logging
from datetime import datetime

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove

from tgbot.keyboards import reply
from tgbot.keyboards.admin_menu import *

from tgbot.keyboards.admin_menu import main_menu_message
from tgbot.misc.misc import user_add_or_update
from tgbot.models.analytic import Prediction, Analytic
from tgbot.models.users import User
from tgbot.state.predict import Analytics


async def add_analytic(message: Message):
    await message.answer("Введите Telegram Id Аналитика!", reply_markup=reply.cancel)
    await Analytics.Check_Analytic.set()


async def add_analytic_button(query: CallbackQuery):
    user: User = await user_add_or_update(query, role='admin', module=__name__)
    await query.answer()
    await query.message.answer("Введите Telegram Id Аналитика!", reply_markup=reply.cancel)
    await Analytics.Check_Analytic.set()

async def cancel(message: Message, state: FSMContext):
    await message.answer('выход из меню добавления аналитика', reply_markup=ReplyKeyboardRemove())
    await state.finish()

async def back_to(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == 'Analytics:Set_Nickname':
        await message.answer('возврат к добавлению Аналитика', reply_markup=ReplyKeyboardRemove())
        await add_analytic(message)
    if current_state == 'Analytics:Publish':
        await message.answer('Возврат к вводу Nickname', reply_markup=ReplyKeyboardRemove())
        async with state.proxy() as data:
            message.text = data['analytic_id']
        await check_analytic(message, state)

async def check_analytic(message: Message, state: FSMContext):
    try:
        analytic_id= int(message.text)
    except ValueError:
        await message.answer('вы ввели неверный telegram ID')
        state = await state.reset_state()
        await add_analytic(message)
        return
    current_state = await state.get_state()
    config = message.bot.get('config')
    db_session = message.bot.get('db')
    analytic: Analytic = await Analytic.get_analytic_by_id(db_session=db_session, telegram_id=analytic_id)
    if not analytic:
        text = f'Введите Nikckname аналитика'
        await message.answer(text, reply_markup=reply.cancel_back_markup)
        await state.update_data(analytic_id=analytic_id)
        await Analytics.Set_Nickname.set()
    else:
        if analytic.is_active == True:
            await message.answer(f"этот пользователь уже является активным Аналитиком\nАналитик: {analytic.Nickname}\nRating: {analytic.rating}")
            state = await state.reset_state()
            await add_analytic(message)
        else:
            text=f'''этот пользователь уже есть в базе Аналитиков, но в данный момент неактивен. 
Для включения роли аналитика для этого пользователя перейдите в меню "Управление Аналитиками\Активировать Аналитика"
Аналитик: {analytic.Nickname}
Rating: {analytic.rating}'''
            await message.answer(text=text)
            state = await state.reset_state()
            await add_analytic(message)

async def set_nickname(message: Message, state: FSMContext):
    nickname = message.text
    if len(nickname) > 30:
        await message.answer('Имя слишком длинное')
        async with state.proxy() as data:
            message.text = data['analytic_id']
        await Analytics.Check_Analytic.set()
        await check_analytic(message, state)
        return
    async with state.proxy() as data:
        data['nickname'] = nickname
        analytic_id = data['analytic_id']
    text=f'''Аналитик: {nickname}
Telegram ID: {analytic_id}
Добавить в базу?'''
    await message.answer(text=text, reply_markup=reply.confirm)
    await Analytics.Publish.set()


async def publish(message: Message, state: FSMContext):
    config = message.bot.get('config')
    async with state.proxy() as data:
        analytic_id = data['analytic_id']
        nickname = data['nickname']
    db_session = message.bot.get('db')
    analytic: Analytic = await Analytic.add_analytic(db_session=db_session,
                                                     telegram_id=analytic_id,
                                                     nickname=nickname)


    text = f'''Аналитик: {nickname}
Telegram ID: {analytic_id}
Добавлен в базу'''
    logger = logging.getLogger(__name__)

    await message.answer(text=text,
                         reply_markup=ReplyKeyboardRemove())
    channel_id = config.tg_bot.channel_id
    logger.info(f'{text}')
    # user: User = await User.get_user(db_session=db_session, telegram_id=analytic_id)
    # if not user:
    #     pass
    # else:
    #     if user.role == 'user':
    #         updated_user: User = await user.update_user(db_session=db_session,
    #                                                 role=analytic,
    #                                                 is_botuser=True)


    await state.finish()




async def admin_start(message: Message):
    user: User = await user_add_or_update(message, role='admin', module=__name__)
    await message.answer(
        f'''Hello, {user.username} - admin !
    /menu - чтобы попасть в основное меню
    /help - Информация.
    ''')

async def menu(message: Message):
    user: User = await user_add_or_update(message, role='admin', module=__name__)
    await message.answer(text=main_menu_message(),
                         reply_markup=main_menu_keyboard())

async def main_menu(query: CallbackQuery):
    user: User = await user_add_or_update(query, role='admin', module=__name__)
    await query.answer()
    await query.message.edit_text(
        text=main_menu_message(),
        reply_markup=main_menu_keyboard())

async def first_menu(query: CallbackQuery):
    user: User = await user_add_or_update(query, role='admin', module=__name__)
    await query.answer()
    await query.message.edit_text(
        text=first_menu_message(),
        reply_markup=first_menu_keyboard())


async def second_menu(query: CallbackQuery):
    user: User = await user_add_or_update(query, role='admin', module=__name__)
    await query.answer()
    await query.message.edit_text(
        text=second_menu_message(),
        reply_markup=second_menu_keyboard())




def register_admin(dp: Dispatcher):
    dp.register_callback_query_handler(main_menu, analytic_callback.filter(action='main'), is_admin=True, state="*")
    dp.register_callback_query_handler(main_menu, admin_callback.filter(action='main'), is_admin=True, state="*")
    dp.register_callback_query_handler(first_menu, admin_callback.filter(action='analytic'), is_admin=True, state="*")
    dp.register_callback_query_handler(add_analytic_button, admin_callback.filter(action='analytic_1'), is_admin=True, state="*")
    dp.register_message_handler(menu, commands=["menu"], state="*", is_admin=True)
    dp.register_message_handler(admin_start, commands=["start"], state="*", is_admin=True)
    dp.register_message_handler(cancel, text="отменить", state=[Analytics.Check_Analytic, Analytics.Set_Nickname, Analytics.Publish])
    dp.register_message_handler(back_to, text="назад", state=[Analytics.Check_Analytic, Analytics.Set_Nickname, Analytics.Publish])
    dp.register_message_handler(add_analytic, text="/analytic", state='*', is_admin=True)
    dp.register_message_handler(set_nickname, state=Analytics.Set_Nickname)
    dp.register_message_handler(check_analytic, state=Analytics.Check_Analytic)
    dp.register_message_handler(publish, text="опубликовать", state=Analytics.Publish)

