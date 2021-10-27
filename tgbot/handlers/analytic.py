import decimal
import logging
from decimal import Decimal

from aiogram import Dispatcher
from datetime import datetime, timedelta
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils.markdown import hcode

from tgbot.handlers.botuser import myinfo
from tgbot.keyboards.analytic_menu import *

from tgbot.models.analytic import Prediction, Analytic
from tgbot.keyboards import reply
from tgbot.models.users import User
from tgbot.state.predict import Predict
from tgbot.misc import tinkoff, bdays


async def menu(message: Message):
    await message.answer(text=main_menu_message(),
                         reply_markup=main_menu_keyboard())


async def main_menu(query: CallbackQuery):
    await query.answer()
    await query.message.edit_text(
        text=main_menu_message(),
        reply_markup=main_menu_keyboard())


async def first_menu(query: CallbackQuery):
    await query.answer()
    await query.message.edit_text(
        text=first_menu_message(),
        reply_markup=first_menu_keyboard())


async def second_menu(query: CallbackQuery):
    await query.answer()
    await query.message.edit_text(
        text=second_menu_message(),
        reply_markup=second_menu_keyboard())

async def analytic_start(message: Message):
    if message.chat.id != message.from_user.id:
        return
    config = message.bot.get('config')
    db_session = message.bot.get('db')
    user_id = message.from_user.id
    firstname = message.from_user.first_name
    username = message.from_user.username
    lastname = message.from_user.last_name

    role = 'analytic'
    user: User = await User.get_user(db_session=db_session,
                                     telegram_id=user_id)
    # запущен ли бот в бесплатном режиме.
    free = config.test.free
    if free:
        subscription_until_str = config.test.free_subtime
    else:
        subscription_until_str = config.test.prod_subtime

    subscription_until = datetime.strptime(subscription_until_str, '%d/%m/%y %H:%M:%S')
    logger = logging.getLogger(__name__)
    if not user:
        new_user: User = await User.add_user(db_session=db_session,
                                             subscription_until=subscription_until,
                                             telegram_id=user_id,
                                             first_name=firstname,
                                             last_name=lastname,
                                             username=username,
                                             role=role,
                                             is_botuser=True,
                                             is_member=False
                                             )
        user: User = await User.get_user(db_session=db_session, telegram_id=user_id)
        logger.info(f'новый аналитик {user.telegram_id}, {user.username}, {user.first_name} зарегестриован в базе')
        logger.info(f'{user.__dict__}')


    else:  # если такой пользователь уже найден - меняем ему статус is_member = true
        updated_user: User = await user.update_user(db_session=db_session,
                                                    role=role,
                                                    is_botuser=True)
        user: User = await User.get_user(db_session=db_session, telegram_id=user_id)
        logger.info(
            f'роль пользователя {user.telegram_id}, {user.username}, {user.first_name} обновлена в базе на Analytic')
        logger.info(f'{user.__dict__}')

    await message.answer(
        f'''Hello, {username} !
    /menu - чтобы попасть в основное меню
    /help - Информация.
    ''')

async def get_invitelink(query: CallbackQuery):
    # если пишут в другой чат, а не боту.
    if query.message.chat.id != query.from_user.id:
        return
    await query.answer()
    config = query.bot.get('config')
    db_session = query.bot.get('db')
    user_id = query.from_user.id
    firstname = query.from_user.first_name
    username = query.from_user.username
    lastname = query.from_user.last_name

    user: User = await User.get_user(db_session=db_session,
                                     telegram_id=user_id)
    # запущен ли бот в бесплатном режиме.
    logger = logging.getLogger(__name__)

    if user.is_member == True:
        await query.message.answer(
            f"Hello, {username} ! \n Вы уже являетесь подписчиком канала. ")
    else:
        invite_link = await query.bot.create_chat_invite_link(chat_id=config.tg_bot.channel_id,
                                                                expire_date=timedelta(hours=1))
        await query.message.answer(
            f"Hello, {username}, Analytic ! \nВаша ссылка для входа в канал: {invite_link.invite_link}")

async def make_predict_button(query: CallbackQuery):
    await query.answer()
    await query.message.answer("Введите название акции!", reply_markup=reply.cancel)
    await Predict.Check_Ticker.set()

async def make_predict(message: Message):
    await message.answer("Введите название акции!", reply_markup=reply.cancel)
    await Predict.Check_Ticker.set()


# async def repeat_predict(query: query, state:FSMContext):
#     await query.text("Введите название акции")
#     print(query.text, query.from_user.username, query.from_user.id)
#     await Predict.Check_Ticker.set()

async def cancel(message: Message, state: FSMContext):
    await message.answer('выход из прогноза', reply_markup=ReplyKeyboardRemove())
    await state.finish()


async def back_to(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == 'Predict:Set_Date':
        await message.answer('возврат к вводу акции', reply_markup=ReplyKeyboardRemove())
        await make_predict(message)
    if current_state == 'Predict:Confirm':
        await message.answer('возврат к вводу даты', reply_markup=ReplyKeyboardRemove())
        async with state.proxy() as data:
            message.text = data['ticker']
        await check_ticker(message, state)
    if current_state == 'Predict:Publish':
        await message.answer('Возврат к вводу цели', reply_markup=ReplyKeyboardRemove())
        async with state.proxy() as data:
            message.text = data['predict_time']
        await set_date(message, state)


async def check_ticker(message: Message, state: FSMContext):
    current_state = await state.get_state()
    ticker = message.text
    db_session = message.bot.get('db')
    prediction: Prediction = await Prediction.get_predict(db_session=db_session, ticker=ticker,
                                                          telegram_id=message.from_user.id)
    config = message.bot.get('config')
    if not prediction:
        instrument = await tinkoff.search_by_ticker(message.text, config)
        if len(instrument) == 0:
            text = f'Такой акции не существует'
            await message.answer(text, reply_markup=reply.cancel_back_markup)
            state = await state.reset_state()
            await make_predict(message)
        else:
            latestcost = await tinkoff.get_latest_cost_history(figi=instrument['figi'], config=config,
                                                               to_time=datetime.utcnow())
            text = f'Курс акции равен {latestcost}.\nВведите срок прогноза в днях(учитываются только торговые дни)'
            await message.answer(text, reply_markup=reply.cancel_back_markup)
            await state.update_data(ticker=ticker.upper())
            await state.update_data(start_value=latestcost)
            await state.update_data(name=instrument['name'])
            await state.update_data(figi=instrument['figi'])
            await state.update_data(currency=instrument['currency'])
            await Predict.Set_Date.set()
    else:
        await message.answer("уже есть активный прогноз по этой акции")
        # await Predict.Predict.set()
        state = await state.reset_state()
        text = [
            f'Эхо в состоянии Analytics {hcode(state)}',
            'Содержание сообщения:',
            hcode(state)
        ]
        await make_predict(message)


async def set_date(message: Message, state: FSMContext):
    try:
        predict_time = int(message.text)
    except ValueError:
        await message.answer('вы ввели неверную дату')
        async with state.proxy() as data:
            message.text = data['ticker']
            print(message.text)
        await Predict.Check_Ticker.set()
        await check_ticker(message, state)
        return

    if predict_time > 20:
        await message.answer('срок прогноза не должен превышать 20 торговых дней')
        async with state.proxy() as data:
            message.text = data['ticker']
        await Predict.Check_Ticker.set()
        await check_ticker(message, state)
        return

    # await message.answer(predict_time)
    async with state.proxy() as data:
        ticker = data['ticker']
        data['predict_time'] = predict_time
        text = [
            f'Ваш Прогноз:',
            f'Акция {ticker} new target'
        ]
    ticker = data['ticker']

    # await state.update_data(predict_time=predict_time)
    await message.answer(f'Введите новую цель акции {ticker}', reply_markup=reply.cancel_back_markup)
    await Predict.Confirm.set()


async def confirm(message: Message, state: FSMContext):
    global target
    try:
        target = float(message.text)
    except ValueError:
        await message.answer('вы ввели неверную цель')
        async with state.proxy() as data:
            message.text = data['predict_time']
        await Predict.Set_Date.set()
        await set_date(message, state)
        return

    async with state.proxy() as data:
        start_value = data['start_value']
    profit = (decimal.Decimal(target) - start_value) * 100 / start_value
    if abs(profit) > 30:
        await message.answer('доходность прогноза не должна привышать 30%.')
        async with state.proxy() as data:
            message.text = data['predict_time']
        await Predict.Set_Date.set()
        print('возвращаюсь в set_date')
        await set_date(message, state)
        return

    if abs(profit) < 3:
        await message.answer('доходность прогноза должна быть меньше 3%.')
        async with state.proxy() as data:
            message.text = data['predict_time']
        await Predict.Set_Date.set()
        await set_date(message, state)
        return

    # await message.answer(message)
    db_session = message.bot.get('db')
    analytic: Analytic = await Analytic.get_analytic_by_id(db_session=db_session, telegram_id=message.from_user.id)
    async with state.proxy() as data:
        data['target'] = target
        data['analytic_nickname'] = analytic.Nickname
        data['analytic_rating'] = analytic.rating
    ticker = data['ticker']
    predict_time = data['predict_time']
    predicted_date = await bdays.next_business_day(datetime.utcnow(), predict_time)
    target = data['target']
    name = data['name']
    currency = data['currency']
    await message.answer(
        f'Акця ${ticker} ({name}), {start_value} {currency} -----> {target} {currency} через {predict_time} торговых дней. ({predicted_date.date()})\n'
        f'Аналитик: {analytic.Nickname}, rating: {analytic.rating}', reply_markup=reply.confirm)
    await Predict.Publish.set()


async def publish(message: Message, state: FSMContext):
    config = message.bot.get('config')
    async with state.proxy() as data:
        ticker = data['ticker']
        name = data['name']
        currency = data['currency']
        predict_time = data['predict_time']
        target = data['target']
        start_value = data['start_value']
        figi = data['figi']
        analytic_nickname = data['analytic_nickname']
        analytic_rating = data['analytic_rating']
        predicted_date = await bdays.next_business_day(datetime.utcnow(), predict_time)
    db_session = message.bot.get('db')
    prediction: Prediction = await Prediction.add_predict(db_session=db_session,
                                                          ticker=ticker,
                                                          name=name,
                                                          currency=currency,
                                                          figi=figi,
                                                          predicted_date=predicted_date,
                                                          start_value=start_value,
                                                          predicted_value=target,
                                                          analytic_id=message.from_user.id)
    days = 'дней'
    if predict_time == 1:
        days = 'день'
    elif predict_time in [2, 3, 4]:
        days = 'дня'

    text = f'''
        ${ticker} ({name})
Цена: {start_value} {currency} --> {target} {currency}
Дата окончания:  {predicted_date.date()}
Аналитик: {analytic_nickname}
Rating: {analytic_rating}'''
    logger = logging.getLogger(__name__)

    await message.answer(text=text,
                         reply_markup=ReplyKeyboardRemove())
    channel_id = config.tg_bot.channel_id
    logger.info(f'{text}')
    await message.bot.send_message(chat_id=channel_id,
                                   text=text)
    await message.bot.send_message(chat_id=channel_id,
                                   text=f'Пульс ${ticker}',
                                   reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                       [
                                           InlineKeyboardButton(text="Open in Tinkoff",
                                                                url=f'https://www.tinkoff.ru/invest/stocks/{ticker}')
                                       ],
                                   ])
                                   )
    await state.finish()


def register_predict(dp: Dispatcher):
    dp.register_callback_query_handler(first_menu, analytic_callback.filter(action='pred'))
    dp.register_callback_query_handler(make_predict_button, analytic_callback.filter(action='pred_1'))
    dp.register_callback_query_handler(get_invitelink, analytic_callback.filter(action='link'))
    #dp.register_callback_query_handler(main_menu, analytic_callback.filter(action='main'))
    dp.register_callback_query_handler(myinfo, analytic_callback.filter(action='myinfo'))
    dp.register_message_handler(menu, commands=["menu"], state="*", is_analytic=True)

    dp.register_message_handler(analytic_start, commands=["start"], state="*", is_analytic=True)
    dp.register_message_handler(cancel, text="отменить",
                                state=[Predict.Check_Ticker, Predict.Set_Date, Predict.Confirm, Predict.Publish])
    dp.register_message_handler(back_to, text="назад", state=[Predict.Set_Date, Predict.Confirm, Predict.Publish])
    dp.register_message_handler(make_predict, text="/predict", state='*', is_analytic=True)
    dp.register_message_handler(check_ticker, state=Predict.Check_Ticker)
    dp.register_message_handler(set_date, state=Predict.Set_Date)
    dp.register_message_handler(confirm, state=Predict.Confirm)
    dp.register_message_handler(publish, text="опубликовать", state=Predict.Publish)
