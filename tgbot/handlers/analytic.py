import decimal
import logging
import math
from decimal import Decimal

from aiogram import Dispatcher
from datetime import datetime, timedelta
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils.markdown import hcode

from tgbot.handlers.botuser import myinfo
from tgbot.keyboards.analytic_menu import *
from tgbot.keyboards.callback_datas import predict_callback, list_my_predicts_callback, user_list_analytic_callback
from tgbot.misc.misc import user_add_or_update

from tgbot.models.analytic import Prediction, Analytic, Prediction_comment
from tgbot.keyboards import reply
from tgbot.models.users import User
from tgbot.state.predict import Predict, Predict_comment
from tgbot.misc import tinkoff, bdays


async def menu(message: Message):
    user: User = await user_add_or_update(message, role='analytic', module=__name__)
    await message.answer(text=main_menu_message(),
                         reply_markup=main_menu_keyboard())


async def main_menu(query: CallbackQuery):
    user: User = await user_add_or_update(query, role='analytic', module=__name__)
    await query.answer()
    await query.message.edit_text(
        text=main_menu_message(),
        reply_markup=main_menu_keyboard())


async def first_menu(query: CallbackQuery):
    user: User = await user_add_or_update(query, role='analytic', module=__name__)
    await query.answer()
    await query.message.edit_text(
        text=first_menu_message(),
        reply_markup=first_menu_keyboard())


async def second_menu(query: CallbackQuery):
    user: User = await user_add_or_update(query, role='analytic', module=__name__)
    await query.answer()
    await query.message.edit_text(
        text=second_menu_message(),
        reply_markup=second_menu_keyboard())


async def analytic_start(message: Message):
    user: User = await user_add_or_update(message, role='analytic', module=__name__)

    await message.answer(
        f'''Hello, {user.username} - Analytic !
    /menu - чтобы попасть в основное меню
    /help - Информация.
    ''')


async def get_invitelink(query: CallbackQuery):
    user: User = await user_add_or_update(query, role='analytic', module=__name__)
    # если пишут в другой чат, а не боту.
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


async def get_predict_list(query: CallbackQuery):
    user: User = await user_add_or_update(query, role='analytic', module=__name__)
    await query.answer()

    db_session = query.bot.get('db')
    logger=logging.getLogger(__name__)
    # список всех предиктов is_active
    predictions: list[Prediction] = await Prediction.get_active_predicts(db_session=db_session)
    markup= InlineKeyboardMarkup(row_width=4)
    db_session = query.bot.get('db')
    active_analytics: list[Analytic] = await Analytic.get_analytics(db_session=db_session, active=True)
    for active_analytic in active_analytics:
        analytic_id = active_analytic.telegram_id
        active_predicts: list[Prediction] = await Prediction.get_predict_by_analytic(db_session=db_session,
                                                                                        analytic_id=analytic_id)
    # for prediction in predictions:
    #     pass
        predictions_long = []
        predictions_short = []
        active_preicts_list = []
        for prediction in active_predicts:
            active_preicts_list.append(prediction)
            target = prediction.predicted_value
            start_value = prediction.start_value
            profit = target - start_value
            sign_profit = math.copysign(1, profit)
            if sign_profit == 1:
                predictions_long.append(prediction)
            elif sign_profit == -1:
                predictions_short.append(prediction)
        prediction_long_buttons = []
        for prediction_long in predictions_long:
            circle = '🟢'
            button_text = f'{circle}${prediction_long.ticker}'
            callback_data = predict_callback.new(ticker=prediction_long.ticker, action="info")
            button = InlineKeyboardButton(text=button_text, callback_data=callback_data)
            prediction_long_buttons.append(button)
            # markup.insert(
            #     InlineKeyboardButton(text=button_text, callback_data=callback_data)
            # )
        prediction_short_buttons = []
        for prediction_short in predictions_short:
            circle = '🔴'
            button_text = f'{circle}${prediction_short.ticker}'
            callback_data = predict_callback.new(ticker=prediction_short.ticker, action="info")
            button = InlineKeyboardButton(text=button_text, callback_data=callback_data)
            prediction_short_buttons.append(button)


            # button_text = f'{circle}${prediction.ticker}'
            # callback_data = user_predict_callback.new(ticker=prediction.ticker)
            # markup.insert(
            #     InlineKeyboardButton(text=button_text, callback_data=callback_data)
            # )
        callback_data = user_list_analytic_callback.new(id=analytic_id, is_active=True, action='list')
        if active_preicts_list != []:
            markup.add(InlineKeyboardButton(text=f'Прогнозы Аналитика 📈{active_analytic.Nickname}', callback_data=callback_data))
        markup.add(*prediction_long_buttons)
        markup.add(*prediction_short_buttons)
    markup.row(
        InlineKeyboardButton('Главное меню', callback_data=analytic_callback.new(action='main'))
    )
    await query.message.edit_text(text='Список активных прогнозов:', reply_markup=markup)

    # config = query.bot.get('config')
    # db_session = query.bot.get('db')
    # logger = logging.getLogger(__name__)
    # # список всех предиктов is_active
    # predictions: list[Prediction] = await Prediction.get_active_predicts(db_session=db_session)
    # markup = InlineKeyboardMarkup(row_width=5)
    # for prediction in predictions:
    #     target = prediction.predicted_value
    #     start_value = prediction.start_value
    #     profit = target - start_value
    #     sign_profit = math.copysign(1, profit)
    #     if sign_profit == -1:
    #         circle = '🔴'
    #     else:
    #         circle = '🟢'
    #     button_text = f'{circle}${prediction.ticker}'
    #     callback_data = predict_callback.new(ticker=prediction.ticker)
    #     markup.insert(
    #         InlineKeyboardButton(text=button_text, callback_data=callback_data)
    #     )
    # markup.row(
    #     InlineKeyboardButton('Main menu', callback_data=analytic_callback.new(action='main'))
    # )
    # await query.message.edit_text(text='Список активных прогнозов:', reply_markup=markup)


async def predict_info(query: CallbackQuery, callback_data: dict):
    config = query.bot.get('config')
    db_session = query.bot.get('db')
    logger = logging.getLogger(__name__)
    await query.answer()
    # logger.info(f"{callback_data}")
    ticker = callback_data.get('ticker')
    # logger.info(f'{ticker}')
    predict = await Prediction.get_predict(db_session=db_session, ticker=ticker)

    currency = predict.currency
    instrument = await tinkoff.search_by_ticker(ticker, config)
    latestcost = await tinkoff.latestcost(figi=instrument['figi'], config=config)
    markup= InlineKeyboardMarkup(row_width=4)
    markup.row(InlineKeyboardButton(text="Cсылка на прогноз", url=f'{predict.message_url}'))
    markup.insert(InlineKeyboardButton(text="Open in Tinkoff", url=f'https://www.tinkoff.ru/invest/stocks/{ticker}'))
    markup.row(InlineKeyboardButton(text='К списку активных прогнозов',
                                    callback_data=predict_callback.new(ticker=ticker, action='back')))
    markup.row(
        InlineKeyboardButton('Главное меню', callback_data=analytic_callback.new(action='main'))
    )
    new_text = await predict.edit_message_text(db_session=db_session)
    new_text += f'\nЦена сейчас: <b>{latestcost} {currency}</b>'
    # await query.message.answer(text=new_text,
    #                                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
    #                                    [
    #                                        InlineKeyboardButton(text="Open in Tinkoff",
    #                                                             url=f'https://www.tinkoff.ru/invest/stocks/{ticker}')
    #                                    ],
    #                                ]))

    await query.message.edit_text(text=new_text, reply_markup=markup)

#     name = predict.name
#     start_value = predict.start_value
#     currency = predict.currency
#     start_date = predict.start_date
#     predicted_date = predict.predicted_date
#     analytic_nickname = predict.analytic.Nickname
#     analytic_rating = predict.analytic.rating
#     target = predict.predicted_value
#     analytic_predicts_total = predict.analytic.predicts_total
#     instrument = await tinkoff.search_by_ticker(ticker, config)
#     latestcost = await tinkoff.latestcost(figi=instrument['figi'], config=config)
#     # latestcost = await tinkoff.get_latest_cost_history(figi=instrument['figi'], config=config,
#     #                                                    to_time=datetime.utcnow()+timedelta(minutes=5))
#     profit = target - start_value
#     sign_profit = math.copysign(1, profit)
#     if sign_profit == -1:
#         circle = '🔴'
#     else:
#         circle = '🟢'
#     text = f'''
#                 🏦<b>${ticker}</b> ({name})
# ⏱Дата начала: <b>{start_date.date():%d-%m-%Y}</b>
# ⏱Дата окончания:  <b>{predicted_date.date():%d-%m-%Y}</b>
# {circle}Прогноз: <b>{start_value} {currency}</b>➡<b>{target} {currency}</b>
# Цена сейчас: <b>{latestcost} {currency}</b>
# Аналитик: <b>{analytic_nickname}</b>
# Рейтинг: <b>{analytic_rating}</b>
# Всего прогнозов: <b>{analytic_predicts_total}</b>'''
#
#     await query.message.answer(text=text,
#                                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
#                                    [
#                                        InlineKeyboardButton(text="Open in Tinkoff",
#                                                             url=f'https://www.tinkoff.ru/invest/stocks/{ticker}')
#                                    ],
#                                ]))


async def make_predict_button(query: CallbackQuery):
    user: User = await user_add_or_update(query, role='analytic', module=__name__)
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
    await message.answer('Выход из прогноза', reply_markup=ReplyKeyboardRemove())
    await state.finish()


async def back_to(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == 'Predict:Set_Date':
        await message.answer('Возврат к вводу акции', reply_markup=ReplyKeyboardRemove())
        await make_predict(message)
    if current_state == 'Predict:Set_Target':
        await message.answer('Возврат к вводу даты', reply_markup=ReplyKeyboardRemove())
        async with state.proxy() as data:
            message.text = data['ticker']
        await check_ticker(message, state)
    if current_state == 'Predict:Set_Risk':
        await message.answer('Возврат к вводу цели', reply_markup=ReplyKeyboardRemove())
        async with state.proxy() as data:
            message.text = data['predict_time']
        await set_date(message, state)
    if current_state == 'Predict:Confirm':
        await message.answer('Возврат к вводу уровня риска', reply_markup=ReplyKeyboardRemove())
        async with state.proxy() as data:
            message.text = data['target']
        await set_target(message, state)
    if current_state == 'Predict:Publish':
        await message.answer('Возврат к вводу коментария', reply_markup=ReplyKeyboardRemove())
        async with state.proxy() as data:
            message.text = data['risk_level']
        await set_risk(message, state)


async def check_ticker(message: Message, state: FSMContext):
    current_state = await state.get_state()
    ticker = message.text
    db_session = message.bot.get('db')
    prediction: Prediction = await Prediction.get_predict(db_session=db_session, ticker=ticker)
    config = message.bot.get('config')
    if not prediction:
        instrument = await tinkoff.search_by_ticker(message.text, config)
        if len(instrument) == 0:
            text = f'Такой акции не существует'
            await message.answer(text, reply_markup=reply.cancel_back_markup)
            state = await state.reset_state()
            await make_predict(message)
        else:
            latestcost = await tinkoff.latestcost(figi=instrument['figi'], config=config)
            # latestcost = await tinkoff.get_latest_cost_history(figi=instrument['figi'], config=config,
            #                                                    to_time=datetime.utcnow()+timedelta(minutes=5))
            latestcost = float(latestcost)
            text = f'''Курс акции равен <b>{latestcost}</b>.
⚠️ВНИМАНИЕ: начальный курс акции будет скоректирован на актуальное значение на шаге подтверждения прогноза.⚠️
Введите срок прогноза в днях(учитываются только торговые дни)
'''
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
    # await Predict.Confirm.set()
    await Predict.Set_Target.set()


async def set_target(message: Message, state: FSMContext):
    config = message.bot.get('config')
    # global target
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
        ticker = data['ticker']
    instrument = await tinkoff.search_by_ticker(ticker, config)
    latestcost = await tinkoff.latestcost(figi=instrument['figi'], config=config)
    # latestcost = await tinkoff.get_latest_cost_history(figi=instrument['figi'], config=config,
    #                                                    to_time=datetime.utcnow()+timedelta(minutes=5))
    start_value = float(latestcost)
    profit = (target - start_value) * 100 / start_value
    if abs(profit) > 30:
        await message.answer('доходность прогноза не должна привышать 30%.')
        async with state.proxy() as data:
            message.text = data['predict_time']
        await Predict.Set_Date.set()
        print('возвращаюсь в set_date')
        await set_date(message, state)
        return

    if abs(profit) < 3:
        await message.answer('доходность прогноза должна быть не меньше 3%.')
        async with state.proxy() as data:
            message.text = data['predict_time']
        await Predict.Set_Date.set()
        await set_date(message, state)
        return

    # await message.answer(message)
    async with state.proxy() as data:
        data['target'] = target
    await message.answer(
        f'Введите уровень риска к прогнозу ${ticker}(по желанию)\n<b>1</b> - низкий уровень риска \n<b>2</b> - средний уровень риска \n<b>3</b> - высокий уровень риска \n',
        reply_markup=reply.cancel_back_markup)
    # await message.answer(f'Введите коментарий к прогнозу ${ticker}(по желанию)\n введите <b>0</b> (ноль) если не хотите оставлять коментарий', reply_markup=reply.cancel_back_markup)
    await Predict.Set_Risk.set()
    # await Predict.Confirm.set()


async def set_risk(message: Message, state: FSMContext):
    config = message.bot.get('config')
    try:
        risk_level = int(message.text)
    except ValueError:
        await message.answer('вы ввели неверное значение уровеня риска\nвозможные значения - 1,2,3')
        async with state.proxy() as data:
            message.text = data['target']
        await Predict.Set_Date.set()
        await set_target(message, state)
        return
    if risk_level not in [1, 2, 3]:
        await message.answer('вы ввели неверное значение уровеня риска\nвозможные значения - 1,2,3')
        async with state.proxy() as data:
            message.text = data['target']
        await Predict.Set_Date.set()
        await set_target(message, state)
        return
    async with state.proxy() as data:
        data['risk_level'] = risk_level
        ticker = data['ticker']
    await message.answer(
        f'Введите коментарий к прогнозу ${ticker}(по желанию)\n введите <b>0</b> (ноль) если не хотите оставлять коментарий',
        reply_markup=reply.cancel_back_markup)
    await Predict.Confirm.set()


async def confirm(message: Message, state: FSMContext):
    config = message.bot.get('config')
    comment = message.text
    async with state.proxy() as data:
        ticker = data['ticker']
    instrument = await tinkoff.search_by_ticker(ticker, config)
    latestcost = await tinkoff.latestcost(figi=instrument['figi'], config=config)
    # latestcost = await tinkoff.get_latest_cost_history(figi=instrument['figi'], config=config,
    #                                                    to_time=datetime.utcnow()+timedelta(minutes=5))
    start_value = float(latestcost)

    db_session = message.bot.get('db')
    analytic: Analytic = await Analytic.get_analytic_by_id(db_session=db_session, telegram_id=message.from_user.id)
    async with state.proxy() as data:
        data['comment'] = comment
        data['analytic_nickname'] = analytic.Nickname
        data['analytic_rating'] = float(analytic.rating)
        data['predicts_total'] = analytic.predicts_total
    risk_level = data['risk_level']
    ticker = data['ticker']
    predict_time = data['predict_time']
    predicted_date = await bdays.next_business_day(datetime.utcnow(), predict_time)
    target = data['target']
    name = data['name']
    currency = data['currency']
    profit = target - start_value
    sign_profit = math.copysign(1, profit)
    if sign_profit == -1:
        circle = '🔴'
    else:
        circle = '🟢'

    risk = '⚡' * risk_level

    if comment == str(0):
        text = f'''
🏦<b>${ticker}</b> ({name})
⏱Дата окончания:  <b>{predicted_date.date():%d-%m-%Y}</b>
{circle}Цена: <b>{start_value} {currency}</b>➡<b>{target} {currency}</b>
⚠️ВНИМАНИЕ: начальный курс акции будет скоректирован на актуальное значение после нажатия на кнопку "опубликовать"⚠
Уровень риска: {risk}
Аналитик: <b>{analytic.Nickname}</b>
Рейтинг: <b>{analytic.rating}</b>
Всего прогнозов: <b>{analytic.predicts_total}</b>'''
    else:
        text = f'''
🏦<b>${ticker}</b> ({name})
⏱Дата окончания:  <b>{predicted_date.date():%d-%m-%Y}</b>
{circle}Цена: <b>{start_value} {currency}</b>➡<b>{target} {currency}</b>
⚠️ВНИМАНИЕ: начальный курс акции будет скоректирован на актуальное значение после нажатия на кнопку "опубликовать"⚠
Уровень риска: {risk}
Аналитик: <b>{analytic.Nickname}</b>
Рейтинг: <b>{analytic.rating}</b>
Всего прогнозов: <b>{analytic.predicts_total}</b>
Коментарий к прогнозу: {comment}'''

    await message.answer(text=text, reply_markup=reply.confirm)
    await Predict.Publish.set()


async def publish(message: Message, state: FSMContext):
    config = message.bot.get('config')
    async with state.proxy() as data:
        comment = data['comment']
        ticker = data['ticker']
        name = data['name']
        currency = data['currency']
        predict_time = data['predict_time']
        target = data['target']
        start_value = data['start_value']
        figi = data['figi']
        analytic_nickname = data['analytic_nickname']
        analytic_rating = data['analytic_rating']
        analytic_predicts_total = data['predicts_total']
        risk_level = data['risk_level']
        predicted_date = await bdays.next_business_day(datetime.utcnow(), predict_time)
        instrument = await tinkoff.search_by_ticker(ticker, config)
        latestcost = await tinkoff.latestcost(figi=instrument['figi'], config=config)
        # latestcost = await tinkoff.get_latest_cost_history(figi=instrument['figi'], config=config,
        #                                                    to_time=datetime.utcnow()+timedelta(minutes=5))
        start_value = float(latestcost)

    profit = target - start_value
    sign_profit = math.copysign(1, profit)
    if sign_profit == -1:
        circle = '🔴'
    else:
        circle = '🟢'
    risk = '⚡' * risk_level

    db_session = message.bot.get('db')
    if comment == str(0):
        text = f'''🏦 <b>${ticker}</b> ({name})
⏱Дата окончания:  <b>{predicted_date.date():%d-%m-%Y}</b>
{circle}Цена: <b>{start_value} {currency}</b>➡<b>{target} {currency}</b>
Уровень риска: {risk}
Аналитик: <b>{analytic_nickname}</b>
Рейтинг: <b>{analytic_rating}</b>
Всего прогнозов: <b>{analytic_predicts_total}</b>'''
    else:
        text = f'''🏦 <b>${ticker}</b> ({name})
⏱Дата окончания:  <b>{predicted_date.date():%d-%m-%Y}</b>
{circle}Цена: <b>{start_value} {currency}</b>➡<b>{target} {currency}</b>
Уровень риска: {risk}
Аналитик: <b>{analytic_nickname}</b>
Рейтинг: <b>{analytic_rating}</b>
Всего прогнозов: <b>{analytic_predicts_total}</b>
Коментарий к прогнозу: {comment}'''
    logger = logging.getLogger(__name__)

    await message.answer(text=text,
                         reply_markup=ReplyKeyboardRemove())
    channel_id = config.tg_bot.channel_id
    logger.info(f'{text}')
    channel_message = await message.bot.send_message(chat_id=channel_id,
                                                     text=text)
    edited_channel_message = await message.bot.edit_message_text(chat_id=channel_id,
                                                                 text=text + f'\nСтатус:📈<b>АКТИВЕН</b>',
                                                                 message_id=channel_message.message_id)
    await message.bot.send_message(chat_id=channel_id,
                                   text=f'Пульс ${ticker}',
                                   reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                       [
                                           InlineKeyboardButton(text="Open in Tinkoff",
                                                                url=f'https://www.tinkoff.ru/invest/stocks/{ticker}')
                                       ],
                                   ])
                                   )
    prediction: Prediction = await Prediction.add_predict(db_session=db_session,
                                                          ticker=ticker,
                                                          name=name,
                                                          currency=currency,
                                                          figi=figi,
                                                          predicted_date=predicted_date,
                                                          start_value=start_value,
                                                          predicted_value=target,
                                                          analytic_id=message.from_user.id,
                                                          message_id=channel_message.message_id,
                                                          message_url=channel_message.url,
                                                          message_text=channel_message.html_text,
                                                          comment=comment,
                                                          risk_level=risk_level
                                                          )
    await state.finish()


async def my_active_predicts(query: CallbackQuery):
    user: User = await user_add_or_update(query, role='analytic', module=__name__)
    await query.answer()
    config = query.bot.get('config')
    db_session = query.bot.get('db')
    analytic_id = query.from_user.id
    # my_active_predicts: list[Prediction] = await Prediction.get_predict_by_analytic(db_session=db_session,
    #                                                                                 analytic_id=analytic_id)

    markup = InlineKeyboardMarkup(row_width=4)
    active_predicts: list[Prediction] = await Prediction.get_predict_by_analytic(db_session=db_session,
                                                                                    analytic_id=analytic_id)
# for prediction in predictions:
#     pass
    predictions_long = []
    predictions_short = []
    active_preicts_list = []
    for prediction in active_predicts:
        active_preicts_list.append(prediction)
        target = prediction.predicted_value
        start_value = prediction.start_value
        profit = target - start_value
        sign_profit = math.copysign(1, profit)
        if sign_profit == 1:
            predictions_long.append(prediction)
        elif sign_profit == -1:
            predictions_short.append(prediction)
    prediction_long_buttons = []
    for prediction_long in predictions_long:
        circle = '🟢'
        button_text = f'{circle}${prediction_long.ticker}'
        callback_data = list_my_predicts_callback.new(ticker=prediction_long.ticker, action='choose')
        button = InlineKeyboardButton(text=button_text, callback_data=callback_data)
        prediction_long_buttons.append(button)
        # markup.insert(
        #     InlineKeyboardButton(text=button_text, callback_data=callback_data)
        # )
    prediction_short_buttons = []
    for prediction_short in predictions_short:
        circle = '🔴'
        button_text = f'{circle}${prediction_short.ticker}'
        callback_data = list_my_predicts_callback.new(ticker=prediction_short.ticker, action='choose')
        button = InlineKeyboardButton(text=button_text, callback_data=callback_data)
        prediction_short_buttons.append(button)


        # button_text = f'{circle}${prediction.ticker}'
        # callback_data = user_predict_callback.new(ticker=prediction.ticker)
        # markup.insert(
        #     InlineKeyboardButton(text=button_text, callback_data=callback_data)
        # )

    markup.add(*prediction_long_buttons)
    markup.add(*prediction_short_buttons)


    #
    # print(my_active_predicts)
    # markup = InlineKeyboardMarkup(row_width=4)
    # for prediction in my_active_predicts:
    #     button_text = f'${prediction.ticker}'
    #     callback_data = list_my_predicts_callback.new(ticker=prediction.ticker, action='choose')
    #     markup.insert(
    #         InlineKeyboardButton(text=button_text, callback_data=callback_data)
    #     )
    markup.row(
        InlineKeyboardButton('Main menu', callback_data=analytic_callback.new(action='main'))
    )
    await query.message.edit_text(text='Список моих активных прогнозов:', reply_markup=markup)


async def choose_action_my_predict(query: CallbackQuery, callback_data: dict):
    user: User = await user_add_or_update(query, role='analytic', module=__name__)
    await query.answer()
    config = query.bot.get('config')
    db_session = query.bot.get('db')
    analytic_id = query.from_user.id
    ticker = callback_data.get('ticker')
    predict = await Prediction.get_predict(db_session=db_session, ticker=ticker)
    new_text = await predict.edit_message_text(db_session=db_session)
    currency = predict.currency
    instrument = await tinkoff.search_by_ticker(ticker, config)
    latestcost = await tinkoff.latestcost(figi=instrument['figi'], config=config)
    new_text += f'\nЦена сейчас: <b>{latestcost} {currency}</b>'
    markup = InlineKeyboardMarkup(row_width=1)
    markup.insert(InlineKeyboardButton(text=f'🚫Отменить прогноз ${ticker}',
                                       callback_data=list_my_predicts_callback.new(ticker=ticker,
                                                                                   action='confirm_delete')))
    markup.insert(InlineKeyboardButton(text=f'📝Добавить коментарий в прогноз ${ticker}',
                                       callback_data=list_my_predicts_callback.new(ticker=ticker,
                                                                                   action='add_comment')))
    markup.row(InlineKeyboardButton(text='К списку моих прогнозов',
                                    callback_data=list_my_predicts_callback.new(ticker=ticker, action='back_to_my')))
    markup.row(
        InlineKeyboardButton('Main menu', callback_data=analytic_callback.new(action='main'))
    )
    await query.message.edit_text(text='Выберите действие для прогноза:' + f'\n{new_text}', reply_markup=markup)


async def confirm_delete_my_predict(query: CallbackQuery, callback_data: dict):
    user: User = await user_add_or_update(query, role='analytic', module=__name__)
    await query.answer()
    config = query.bot.get('config')
    db_session = query.bot.get('db')
    analytic_id = query.from_user.id
    ticker = callback_data.get('ticker')
    markup = InlineKeyboardMarkup(row_width=3)
    markup.insert(InlineKeyboardButton(text=f'ДА, отменить ${ticker}',
                                       callback_data=list_my_predicts_callback.new(ticker=ticker,
                                                                                   action='delete')))
    markup.row(InlineKeyboardButton(text='НЕТ, к списку моих прогнозов',
                                    callback_data=list_my_predicts_callback.new(ticker=ticker, action='back_to_my')))
    markup.row(
        InlineKeyboardButton('Main menu', callback_data=analytic_callback.new(action='main'))
    )
    await query.message.edit_text(text=f'Точно отменить прогноз ${ticker}?', reply_markup=markup)


async def delete_my_predict(query: CallbackQuery, callback_data: dict):
    user: User = await user_add_or_update(query, role='analytic', module=__name__)
    await query.answer()
    config = query.bot.get('config')
    db_session = query.bot.get('db')
    analytic_id = query.from_user.id
    ticker = callback_data.get('ticker')

    predict = await Prediction.get_predict_analytic_ticker(db_session=db_session,
                                                           ticker=ticker,
                                                           analytic_id=analytic_id)
    name = predict.name
    start_value = predict.start_value
    currency = predict.currency
    start_date = predict.start_date
    predicted_date = predict.predicted_date
    analytic_nickname = predict.analytic.Nickname
    analytic_rating = predict.analytic.rating
    target = predict.predicted_value
    analytic_predicts_total = predict.analytic.predicts_total
    instrument = await tinkoff.search_by_ticker(ticker, config)
    latestcost = await tinkoff.latestcost(figi=instrument['figi'], config=config)
    # latestcost = await tinkoff.get_latest_cost_history(figi=instrument['figi'], config=config,
    #                                                    to_time=datetime.utcnow())
    analytic = await Analytic.get_analytic_by_id(db_session=db_session, telegram_id=analytic_id)
    end_value = latestcost
    end_date = datetime.utcnow()
    await Prediction.update_predict(db_session,
                                    successful=False,
                                    end_value=end_value,
                                    end_date=end_date,
                                    id=predict.id)
    updated_predict = await Prediction.get_predict_analytic_ticker(db_session=db_session,
                                                                   ticker=ticker,
                                                                   analytic_id=analytic_id)

    prediction_rating = await updated_predict.calculate_rating(analytic)
    try:
        if analytic.bonuscount > 0:
            bonuscount = analytic.bonuscount - 1
            if bonuscount == 0:
                await analytic.update_analytic(db_session=db_session, bonus=0, bonuscount=0)
            else:
                await analytic.update_analytic(db_session=db_session, bonuscount=bonuscount)
    except TypeError:
        pass

    new_rating = await analytic.calculate_rating(prediction_rating)

    await Analytic.set_analytic_rating(db_session, rating=new_rating, telegram_id=analytic_id)
    await Prediction.update_predict_rating(db_session, id=predict.id, rating=prediction_rating)
    updated_prediction = await Prediction.get_predict_by_id(db_session=db_session,
                                                            id=predict.id)
    updated_analytic = await Analytic.get_analytic_by_id(db_session=db_session, telegram_id=analytic_id)
    # new_text=updated_prediction.message_text
    new_text = await updated_prediction.edit_message_text(db_session=db_session)
    message_id = updated_prediction.message_id
    message_url = updated_prediction.message_url

    profit = target - start_value
    sign_profit = math.copysign(1, profit)
    if sign_profit == -1:
        circle = '🔴'
    else:
        circle = '🟢'
    text = f'''Прогноз был отменен
    🏦<b>${ticker}</b> ({name})
    ⏱Дата начала: <b>{start_date.date():%d-%m-%Y}</b>                 
    ⏱Дата окончания:  <b>{predicted_date.date():%d-%m-%Y}</b>
    {circle}Прогноз: <b>{start_value} {currency}</b>➡<b>{target} {currency}</b>
    Цена сейчас: <b>{latestcost} {currency}</b>
    Аналитик: <b>{analytic_nickname}</b>
    Новый рейтинг аналитика: <b>{new_rating}</b>'''

    if not message_id:
        text_tochannel = f'''🚫🚫🚫Прогноз по акции <b>${updated_prediction.ticker}</b> БЫЛ ОТМЕНЕН!!! . 
🏦Прогноз:<b>{updated_prediction.start_value} {updated_prediction.currency}</b>➡<b>{updated_prediction.predicted_value} {updated_prediction.currency}</b>
Фактическое изменение: <b>{updated_prediction.start_value} {updated_prediction.currency}</b>➡<b>{updated_prediction.end_value} {updated_prediction.currency}</b>
Рейтинг прогноза: <b>{updated_prediction.rating}</b>
Рейтинг аналитика <b>{analytic.Nickname}</b>: <b>{analytic.rating}</b>➡<b>{updated_analytic.rating}</b>
Всего прогнозов: <b>{updated_analytic.predicts_total}</b>.'''
        markup = InlineKeyboardMarkup(row_width=3)
        markup.insert(InlineKeyboardButton(text='К списку моих прогнозов',
                                           callback_data=list_my_predicts_callback.new(ticker=ticker, action='back_to_my')))
        markup.row(
            InlineKeyboardButton('Main menu', callback_data=analytic_callback.new(action='main'))
        )
        # await query.message.answer(text=text)
        channel_id = config.tg_bot.channel_id
        await query.message.edit_text(text=text, reply_markup=markup)
        await query.message.bot.send_message(chat_id=channel_id,
                                             text=text_tochannel)
    else:
        # new_text = new_text.replace("&lt;", "<").replace("&gt;", ">")
        text_tochannel = f'''🚫🚫🚫Прогноз по акции <b><a href="{message_url}">${updated_prediction.ticker}</a></b> БЫЛ ОТМЕНЕН!!! . 
🏦Прогноз:<b>{updated_prediction.start_value} {updated_prediction.currency}</b>➡<b>{updated_prediction.predicted_value} {updated_prediction.currency}</b>
Фактическое изменение: <b>{updated_prediction.start_value} {updated_prediction.currency}</b>➡<b>{updated_prediction.end_value} {updated_prediction.currency}</b>
Рейтинг прогноза: <b>{updated_prediction.rating}</b>
Рейтинг аналитика <b>{analytic.Nickname}</b>: <b>{analytic.rating}</b>➡<b>{updated_analytic.rating}</b>
Всего прогнозов: <b>{updated_analytic.predicts_total}</b>.'''
        markup = InlineKeyboardMarkup(row_width=3)
        markup.insert(InlineKeyboardButton(text='К списку моих прогнозов',
                                           callback_data=list_my_predicts_callback.new(ticker=ticker, action='back_to_my')))
        markup.row(
            InlineKeyboardButton('Main menu', callback_data=analytic_callback.new(action='main'))
        )
        # await query.message.answer(text=text)
        channel_id = config.tg_bot.channel_id
        await query.message.edit_text(text=text, reply_markup=markup)

        channel_message = await query.message.bot.send_message(chat_id=channel_id, text=text_tochannel)
        await query.message.bot.edit_message_text(
            text=new_text + f'\nСтатус: <b>🚫<a href="{channel_message.url}">ОТМЕНЕН</a></b>', chat_id=channel_id,
            message_id=message_id)

        # await query.message.bot.send_message(chat_id=channel_id,
        #                                text=text_tochannel)


async def cancel_comment(message: Message, state: FSMContext):
    await message.answer('выход из коментария', reply_markup=ReplyKeyboardRemove())
    await state.finish()


async def comment_back_to(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == 'Predict_comment:Publish_Comment':
        await message.answer('Возврат к вводу коментария', reply_markup=ReplyKeyboardRemove())
        query: CallbackQuery = CallbackQuery()
        callback_data = {}
        async with state.proxy() as data:
            callback_data['ticker'] = data['ticker']
        await add_comment_my_predict(query=query, callback_data=callback_data)
    # if current_state == 'Predict:Set_Target':
    #     await message.answer('Возврат к вводу даты', reply_markup=ReplyKeyboardRemove())
    #     async with state.proxy() as data:
    #         message.text = data['ticker']
    #     await check_ticker(message, state)
    # if current_state == 'Predict:Confirm':
    #     await message.answer('Возврат к вводу цели', reply_markup=ReplyKeyboardRemove())
    #     async with state.proxy() as data:
    #         message.text = data['predict_time']
    #     await set_date(message, state)
    # if current_state == 'Predict:Publish':
    #     await message.answer('Возврат к вводу коментария', reply_markup=ReplyKeyboardRemove())
    #     async with state.proxy() as data:
    #         message.text = data['target']
    #     await set_target(message, state)


async def add_comment_my_predict(query: CallbackQuery, callback_data: dict):
    user: User = await user_add_or_update(query, role='analytic', module=__name__)
    await query.answer()
    await Predict_comment.Set_Comment.set()
    state = Dispatcher.get_current().current_state()
    config = query.bot.get('config')
    db_session = query.bot.get('db')
    analytic_id = query.from_user.id
    ticker = callback_data.get('ticker')
    prediction = await Prediction.get_predict_analytic_ticker(db_session=db_session,
                                                              ticker=ticker,
                                                              analytic_id=analytic_id)

    comments_raw = await Prediction_comment.get_comments_by_predict(db_session=db_session, prediction_id=prediction.id)
    comments = []
    max_comments = 3
    comment_count = 0
    for comment in comments_raw:
        print(comment)
        comments.append(comment)
        comment_count += 1
        print(comments)
    comments_avaliable = max_comments - comment_count
    if comments_avaliable <= 0:
        await query.message.answer(f'К прогнозу нельзя добавить больше {max_comments}х коментариев',
                                   reply_markup=ReplyKeyboardRemove())
        await state.finish()
        return
    start = f'{prediction.start_date.date():%d-%m-%Y}'
    async with state.proxy() as data:
        data['ticker'] = ticker
        data['analytic_id'] = analytic_id
        data['analytic_nickname'] = prediction.analytic.Nickname
        data['start_date'] = start
        data['prediction_url'] = prediction.message_url
        data['prediction_id'] = prediction.id
        data['message_id'] = prediction.message_id
        data['message_text'] = prediction.message_text
    await query.message.answer(f'Вы можете оставить еще {comments_avaliable} коментария к прогнозу <b>${ticker}</b>\n'
                               f'Введите текст коментария:', reply_markup=reply.cancel)
    await Predict_comment.Confirm.set()


async def set_comment_my_predict(message: Message, state: FSMContext):
    config = message.bot.get('config')
    comment = message.text
    async with state.proxy() as data:
        ticker = data['ticker']
        analytic_nickname = data['analytic_nickname']
        data['comment'] = comment
        start_date = data['start_date']
        prediction_url = data['prediction_url']
    channel_id = config.tg_bot.channel_id

    text = f'''Аналитик <b>{analytic_nickname}</b> добавил коментарий к прогнозу по акции \n🏦<b><a href="{prediction_url}">${ticker}</a></b> от <b>{start_date}</b>   :
{comment}'''

    async with state.proxy() as data:
        data['text'] = text
        data['comment'] = comment

    await message.answer(text=f'<b>Текст опубликованного сообщения будет:</b>\n' + text,
                         reply_markup=reply.confirm_no_back)
    await Predict_comment.Publish_Comment.set()
    # channel_message = await message.bot.send_message(chat_id=channel_id,
    #                                text=comment)


async def publish_comment(message: Message, state: FSMContext):
    config = message.bot.get('config')
    async with state.proxy() as data:
        text_tochannel = data['text']
        analytic_nickname = data['analytic_nickname']
        prediction_id = data['prediction_id']
        comment = data['comment']
        message_id = data['message_id']
        message_text = data['message_text']
    channel_id = config.tg_bot.channel_id
    await message.answer(text=text_tochannel,
                         reply_markup=ReplyKeyboardRemove())
    channel_message = await message.bot.send_message(chat_id=channel_id,
                                                     text=text_tochannel)
    db_session = message.bot.get('db')
    prediction_comment = await Prediction_comment.add_prediction_comment(db_session=db_session,
                                                                         prediction_id=prediction_id,
                                                                         comment=comment,
                                                                         message_id=channel_message.message_id,
                                                                         message_url=channel_message.url
                                                                         )

    prediction: Prediction = await Prediction.get_predict_by_id(db_session=db_session, id=prediction_id)
    new_text = await prediction.edit_message_text(db_session=db_session)

    # new_text = message_text + f'\nДобавлен коментарий:'
    await message.bot.edit_message_text(text=new_text + f'\nСтатус:📈<b>АКТИВЕН</b>',
                                        chat_id=channel_id, message_id=message_id)

    await state.finish()


def register_analytic(dp: Dispatcher):
    dp.register_callback_query_handler(first_menu, analytic_callback.filter(action='pred'), is_analytic=True, state="*", chat_type="private")
    dp.register_callback_query_handler(make_predict_button, analytic_callback.filter(action='pred_1'), is_analytic=True, state="*", chat_type="private")
    dp.register_callback_query_handler(get_invitelink, analytic_callback.filter(action='link'),  is_analytic=True, state="*", chat_type="private")
    dp.register_callback_query_handler(get_predict_list, analytic_callback.filter(action='pred_2'), is_analytic=True, state="*", chat_type="private")
    dp.register_callback_query_handler(get_predict_list, predict_callback.filter(action="back"), is_analytic=True, state="*", chat_type="private")
    dp.register_callback_query_handler(my_active_predicts,  analytic_callback.filter(action='pred_3'), is_analytic=True, state="*", chat_type="private")
    dp.register_callback_query_handler(my_active_predicts, list_my_predicts_callback.filter(action="back_to_my"), is_analytic=True, state="*", chat_type="private")
    dp.register_callback_query_handler(choose_action_my_predict, list_my_predicts_callback.filter(action='choose'), is_analytic=True, state="*", chat_type="private")
    dp.register_callback_query_handler(confirm_delete_my_predict, list_my_predicts_callback.filter(action='confirm_delete'), is_analytic=True, state="*", chat_type="private")
    # dp.register_message_handler(comment_back_to, text="назад", state=Predict_comment.Publish_Comment)
    dp.register_message_handler(cancel_comment, text="отменить",
                                state=[Predict_comment.Set_Comment, Predict_comment.Confirm, Predict_comment.Publish_Comment])
    dp.register_callback_query_handler(add_comment_my_predict, list_my_predicts_callback.filter(action='add_comment'), is_analytic=True, state="*", chat_type="private")
    dp.register_message_handler(set_comment_my_predict, state=Predict_comment.Confirm, chat_type="private")
    dp.register_message_handler(publish_comment, text="опубликовать", state=Predict_comment.Publish_Comment, chat_type="private")
    dp.register_callback_query_handler(delete_my_predict, list_my_predicts_callback.filter(action='delete'), is_analytic=True, state="*", chat_type="private")

    dp.register_callback_query_handler(main_menu, analytic_callback.filter(action='main'), is_analytic=True, state="*", chat_type="private")
    dp.register_callback_query_handler(myinfo, analytic_callback.filter(action='myinfo'), state="*", chat_type="private")
    dp.register_message_handler(menu, commands=["menu"], state="*", is_analytic=True, chat_type="private")
    dp.register_callback_query_handler(predict_info, predict_callback.filter(action="info"), is_analytic=True, state="*", chat_type="private")
    dp.register_message_handler(analytic_start, commands=["start"], state="*", is_analytic=True, chat_type="private")
    dp.register_message_handler(cancel, text="отменить",
                                state=[Predict.Check_Ticker, Predict.Set_Date, Predict.Confirm, Predict.Publish, Predict.Set_Target, Predict.Set_Risk])

    dp.register_message_handler(back_to, text="назад", state=[Predict.Set_Date, Predict.Confirm, Predict.Publish, Predict.Set_Target, Predict.Set_Risk])
    dp.register_message_handler(make_predict, text="/predict", state='*', is_analytic=True)
    dp.register_message_handler(check_ticker, state=Predict.Check_Ticker)
    dp.register_message_handler(set_date, state=Predict.Set_Date)
    dp.register_message_handler(set_target, state=Predict.Set_Target)
    dp.register_message_handler(set_risk, state=Predict.Set_Risk)
    dp.register_message_handler(confirm, state=Predict.Confirm)
    dp.register_message_handler(publish, text="опубликовать", state=Predict.Publish)
