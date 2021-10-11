import decimal
from decimal import Decimal

from aiogram import Dispatcher
from datetime import datetime, timedelta
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.utils.markdown import hcode
from sqlalchemy import MetaData

from tgbot.models.analytic import Prediction, Analytic
from tgbot.keyboards import reply
from tgbot.state.predict import Predict
from tgbot.misc import tinkoff


async def make_predict(message: Message):
    await message.answer("Введите название акции!", reply_markup=reply.cancel)
    print(message.text, message.from_user.username, message.from_user.id)
    await Predict.Check_Ticker.set()


# async def repeat_predict(message: Message, state:FSMContext):
#     await message.text("Введите название акции")
#     print(message.text, message.from_user.username, message.from_user.id)
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
            print(message.text)
        await check_ticker(message, state)
    if current_state == 'Predict:Publish':
        await message.answer('Возврат к вводу цели', reply_markup=ReplyKeyboardRemove())
        async with state.proxy() as data:
            message.text = data['predict_time']
        await set_date(message, state)


async def check_ticker(message: Message, state: FSMContext):
    current_state = await state.get_state()
    print(current_state)
    ticker = message.text
    db_session = message.bot.get('db')
    prediction: Prediction = await Prediction.get_predict(db_session=db_session, ticker=ticker,
                                                          telegram_id=message.from_user.id)
    config = message.bot.get('config')
    if not prediction:
        instrument = await tinkoff.search_by_ticker(message.text, config)
        print(instrument)
        if len(instrument) == 0:
            text = f'Такой акции не существует'
            await message.answer(text, reply_markup=reply.cancel_back_markup)
            state = await state.reset_state()
            await make_predict(message)
        else:
            print('акция найдена')
            latestcost = await tinkoff.get_latest_cost_history(figi=instrument['figi'], config=config, to_time=datetime.utcnow())
            text = f'Курс акции равен {latestcost} введис срок прогноза в днях'
            await message.answer(text, reply_markup=reply.cancel_back_markup)
            await state.update_data(ticker=ticker.upper())
            await state.update_data(start_value=latestcost)
            await state.update_data(name=instrument['name'])
            await state.update_data(figi=instrument['figi'])
            await state.update_data(currency=instrument['currency'])
            await Predict.Set_Date.set()
    else:
        print(prediction.__dict__)
        print(prediction.analytic.__dict__)
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
    async with state.proxy() as data:
        print(f'я в Set_date  message: {message.text}, state: {data.state}')

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

    if predict_time > 30:
        await message.answer('срок прогноза не должен превышать 30 дней')
        async with state.proxy() as data:
            message.text = data['ticker']
            print(message.text)
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
    print(f'я тут')
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
        print('возвращаюсь в set_date')
        await set_date(message, state)
        return

    async with state.proxy() as data:
        start_value = data['start_value']
    profit = (decimal.Decimal(target)-start_value)*100/start_value
    print(profit)
    if profit > 30:
        await message.answer('доходность прогноза не должна привышать 30%.')
        async with state.proxy() as data:
            message.text = data['predict_time']
        await Predict.Set_Date.set()
        print('возвращаюсь в set_date')
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
    target = data['target']
    name = data['name']
    currency = data['currency']
    await message.answer(f'Акця ${ticker} ({name}), {start_value} {currency} -----> {target} {currency} через {predict_time} дней.\n'
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
    db_session = message.bot.get('db')
    prediction: Prediction = await Prediction.add_predict(db_session=db_session,
                                                          ticker=ticker,
                                                          name=name,
                                                          currency=currency,
                                                          figi=figi,
                                                          predicted_date=(
                                                                  datetime.utcnow() + timedelta(days=predict_time)),
                                                          start_value=start_value,
                                                          predicted_value=target,
                                                          analytic_id=message.from_user.id)
    print(prediction.__dict__)


    await message.answer(f'Акця ${ticker} ({name}), {start_value} {currency} -----> {target} {currency} через {predict_time} дней.\n'
                         f'Аналитик: {analytic_nickname}, rating: {analytic_rating}',
                         reply_markup=ReplyKeyboardRemove())
    channel_id=config.tg_bot.channel_id
    await message.bot.send_message(chat_id=channel_id,
                                   text=f'Акця ${ticker} ({name}), {start_value} {currency} -----> {target} {currency} через {predict_time} дней.\n'
                         f'Аналитик: {analytic_nickname}, rating: {analytic_rating}')
    await state.finish()


def register_predict(dp: Dispatcher):
    dp.register_message_handler(cancel, text="отменить",
                                state=[Predict.Check_Ticker, Predict.Set_Date, Predict.Confirm, Predict.Publish])
    dp.register_message_handler(back_to, text="назад", state=[Predict.Set_Date, Predict.Confirm, Predict.Publish])
    dp.register_message_handler(make_predict, text="/predict", state='*', is_analytic=True)
    dp.register_message_handler(check_ticker, state=Predict.Check_Ticker)
    dp.register_message_handler(set_date, state=Predict.Set_Date)
    dp.register_message_handler(confirm, state=Predict.Confirm)
    dp.register_message_handler(publish, text="опубликовать", state=Predict.Publish)
