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
from tgbot.keyboards.callback_datas import predict_callback
from tgbot.misc.misc import user_add_or_update

from tgbot.models.analytic import Prediction, Analytic
from tgbot.keyboards import reply
from tgbot.models.users import User
from tgbot.state.predict import Predict
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
    config = query.bot.get('config')
    db_session = query.bot.get('db')
    logger=logging.getLogger(__name__)
    # список всех предиктов is_active
    predictions: list[Prediction] = await Prediction.get_active_predicts(db_session=db_session)
    markup= InlineKeyboardMarkup(row_width=5)
    for prediction in predictions:
        button_text = f'${prediction.ticker}'
        callback_data = predict_callback.new(ticker=prediction.ticker)
        markup.insert(
            InlineKeyboardButton(text=button_text, callback_data=callback_data)
        )
    markup.row(
        InlineKeyboardButton('Main menu', callback_data=analytic_callback.new(action='main'))
    )
    await query.message.edit_text(text='Список активных прогнозов:', reply_markup=markup)


async def predict_info(query: CallbackQuery, callback_data: dict):
    config = query.bot.get('config')
    db_session = query.bot.get('db')
    logger=logging.getLogger(__name__)
    await query.answer()
    logger.info(f"{callback_data}")
    ticker=callback_data.get('ticker')
    logger.info(f'{ticker}')
    predict = await Prediction.get_predict(db_session=db_session, ticker=ticker)
    name = predict.name
    start_value = predict.start_value
    currency = predict.currency
    start_date = predict.start_date
    predicted_date = predict.predicted_date
    analytic_nickname = predict.analytic.Nickname
    analytic_rating = predict.analytic.rating
    target = predict.predicted_value
    analytic_predicts_total=predict.analytic.predicts_total
    instrument = await tinkoff.search_by_ticker(ticker, config)
    latestcost = await tinkoff.get_latest_cost_history(figi=instrument['figi'], config=config,
                                                       to_time=datetime.utcnow())
    text = f'''
                🏦${ticker} ({name})
⏱Дата начала: {start_date.date():%d-%m-%Y}                 
⏱Дата окончания:  {predicted_date.date():%d-%m-%Y}
Прогноз: {start_value} {currency}➡{target} {currency}
Цена сейчас: {latestcost} {currency}
Аналитик: {analytic_nickname}
Рейтинг: {analytic_rating}
Всего прогнозов: {analytic_predicts_total}'''

    await query.message.answer(text=text,
                                   reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                       [
                                           InlineKeyboardButton(text="Open in Tinkoff",
                                                                url=f'https://www.tinkoff.ru/invest/stocks/{ticker}')
                                       ],
                                   ]))


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
        data['predicts_total'] = analytic.predicts_total
    ticker = data['ticker']
    predict_time = data['predict_time']
    predicted_date = await bdays.next_business_day(datetime.utcnow(), predict_time)
    target = data['target']
    name = data['name']
    currency = data['currency']

    text = f'''
            🏦${ticker} ({name})
⏱Дата окончания:  {predicted_date.date():%d-%m-%Y}
Цена: {start_value} {currency}➡{target} {currency}
Аналитик: {analytic.Nickname}
Рейтинг: {analytic.rating}
Всего прогнозов: {analytic.predicts_total}'''


    await message.answer(text=text, reply_markup=reply.confirm)
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
        analytic_predicts_total = data['predicts_total']
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
    text = f'''
        🏦${ticker} ({name})
⏱Дата окончания:  {predicted_date.date():%d-%m-%Y}
Цена: {start_value} {currency}➡{target} {currency}
Аналитик: {analytic_nickname}
Рейтинг: {analytic_rating}
Всего прогнозов: {analytic_predicts_total}'''
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


def register_analytic(dp: Dispatcher):
    dp.register_callback_query_handler(first_menu, analytic_callback.filter(action='pred'), is_analytic=True, state="*", chat_type="private")
    dp.register_callback_query_handler(make_predict_button, analytic_callback.filter(action='pred_1'), is_analytic=True, state="*", chat_type="private")
    dp.register_callback_query_handler(get_invitelink, analytic_callback.filter(action='link'),  is_analytic=True, state="*", chat_type="private")
    dp.register_callback_query_handler(get_predict_list, analytic_callback.filter(action='pred_2'), is_analytic=True, state="*", chat_type="private")
    dp.register_callback_query_handler(main_menu, analytic_callback.filter(action='main'), is_analytic=True, state="*", chat_type="private")
    dp.register_callback_query_handler(myinfo, analytic_callback.filter(action='myinfo'), state="*", chat_type="private")
    dp.register_message_handler(menu, commands=["menu"], state="*", is_analytic=True, chat_type="private")
    dp.register_callback_query_handler(predict_info, predict_callback.filter(), is_analytic=True, state="*", chat_type="private")
    dp.register_message_handler(analytic_start, commands=["start"], state="*", is_analytic=True, chat_type="private")
    dp.register_message_handler(cancel, text="отменить",
                                state=[Predict.Check_Ticker, Predict.Set_Date, Predict.Confirm, Predict.Publish])
    dp.register_message_handler(back_to, text="назад", state=[Predict.Set_Date, Predict.Confirm, Predict.Publish])
    dp.register_message_handler(make_predict, text="/predict", state='*', is_analytic=True)
    dp.register_message_handler(check_ticker, state=Predict.Check_Ticker)
    dp.register_message_handler(set_date, state=Predict.Set_Date)
    dp.register_message_handler(confirm, state=Predict.Confirm)
    dp.register_message_handler(publish, text="опубликовать", state=Predict.Publish)
