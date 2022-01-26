import asyncio
import decimal
import math
import pprint
from datetime import datetime, timedelta
from random import randint

import aiogram
import pytz
from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.exceptions import BotBlocked
from tinvest import Candle

from tgbot.config import load_config, Config
from tgbot.misc.tinkoff import get_candles_inrange
from tgbot.models.analytic import Analytic, Prediction
from tgbot.services.database import create_db_session
from tgbot.misc import tinkoff


async def check_predicts():
    pass

    # пройтись по всем активным предиктам (is_active, end_date = none, predicted_date + 1day < datetime.now())
    #     получить максимальное значение предикта за промежуток.  end_date = datetime.now -1
    #     записываем максимальное значение.

    ####получить список всех активных предиктов (is active, end_date = none)


class PredictionAnalys():
    def __init__(self,
                 best_candle,
                 first_candle_morethen_predicted,
                 prediction_index,
                 worst_candle,
                 first_candle_lessthen_stop,
                 stop_index):
        self.best_candle = best_candle
        self.first_candle_morethen_predicted = first_candle_morethen_predicted
        self.prediction_index = prediction_index
        self.worst_candle = worst_candle
        self.first_candle_lessthen_stop = first_candle_lessthen_stop
        self.stop_index = stop_index

    best_candle: Candle
    first_candle_morethen_predicted: Candle
    prediction_index: decimal
    worst_candle: Candle
    first_candle_lessthen_stop: Candle
    stop_index: decimal


async def predictions_active():
    config: Config = load_config()
    db_session = await create_db_session(config)
    # список всех предиктов is_active
    predictions: list[Prediction] = await Prediction.get_active_predicts(db_session=db_session)
    for prediction in predictions:
        #print(f' предикт: прогнозируемое значение: {prediction.predicted_value}. {prediction}, {prediction.__dict__}')
        to_date = prediction.start_date
        isLong = math.copysign(1, (prediction.predicted_value - prediction.start_value))
        #print(to_date)
        predictionanalysis: PredictionAnalys = await prediction_candle_analys(prediction, config)

        if not predictionanalysis:
            continue
        # если время предикта истекло. учитывая, что таск запускается на следующий день утром после подсчета свечи.
        if prediction.predicted_date <= datetime.now():
            # если предикт всё таки сбылся (индекс 0 или отрицательный)
            if predictionanalysis.prediction_index <= 0:
                # записываем дату первой "пробивной" свечи, в которойпредикт сбылся
                end_date = predictionanalysis.first_candle_morethen_predicted.time.replace(tzinfo=None)
                # конечное значение равно предсказанному
                end_value = prediction.predicted_value
                successful = True
                await Prediction.update_predict(db_session,
                                                successful=successful,
                                                end_value=end_value,
                                                end_date=end_date,
                                                id=prediction.id)
                # print(f'ЗАВЕРШЕННЫЙ ПРЕДИКТ ИЗМЕНЕН В БАЗЕ: {prediction.__dict__}')
                #print(f'прогноз сбылся: {type(end_date)}')
            else:  # если не сбылся - записываем лучшее значение
                # записываем изначальную дату прогноза.
                end_date = prediction.predicted_date
                end_value = await tinkoff.get_latest_cost_history(figi=prediction.figi,
                                                                  config=config,
                                                                  to_time=prediction.predicted_date)
                # if isLong > 0:
                #     end_value = predictionanalysis.best_candle.h
                # else:
                #     end_value = predictionanalysis.best_candle.l
                successful = False
                await Prediction.update_predict(db_session,
                                                successful=successful,
                                                end_value=end_value,
                                                end_date=end_date,
                                                id=prediction.id)
                # print(f'ЗАВЕРШЕННЫЙ ПРЕДИКТ ИЗМЕНЕН В БАЗЕ: {prediction.__dict__}')
                #print(f'максимальное значение за этот период: {end_value}')
                #print(f'прогноз не сбылся: {end_date.date()}')

        else:  # если скро предикта еще не истек
            if predictionanalysis.prediction_index <= 0:
                end_date = predictionanalysis.first_candle_morethen_predicted.time.replace(tzinfo=None)
                #print(f'прогноз сбылся раньше времени{type(end_date)}')
                end_value = prediction.predicted_value
                successful = True
                await Prediction.update_predict(db_session,
                                                successful=successful,
                                                end_value=end_value,
                                                end_date=end_date,
                                                id=prediction.id)
                # print(f'ЗАВЕРШЕННЫЙ ПРЕДИКТ ИЗМЕНЕН В БАЗЕ: {prediction.__dict__}')

            else:
                if predictionanalysis.stop_index >= 0:
                    end_date = predictionanalysis.first_candle_lessthen_stop.time.replace(tzinfo=None)
                    # print(f'прогноз сбылся раньше времени{type(end_date)}')
                    end_value = prediction.stop_value
                    successful = False
                    stopped = True
                    await Prediction.update_predict(db_session,
                                                    successful=successful,
                                                    end_value=end_value,
                                                    end_date=end_date,
                                                    id=prediction.id,
                                                    stopped = stopped)
                ##обработка автостопа не нужна, т.к. стопы будут выставляться всегда на этапе создания прогноза
                # elif predictionanalysis.autostop_index >= 0 and prediction.stopped == False:
                #     end_date = predictionanalysis.first_candle_lessthen_autostop.time.replace(tzinfo=None)
                #     # print(f'прогноз сбылся раньше времени{type(end_date)}')
                #     end_value = predictionanalysis.autostop_value
                #     successful = False
                #     stopped = True
                #     await Prediction.update_predict(db_session,
                #                                     successful=successful,
                #                                     end_value=end_value,
                #                                     end_date=end_date,
                #                                     id=prediction.id,
                #                                     stopped = stopped)


# if predict-date + 1day < datetime.now() (срок прогноза истёк):


# if prediction.predicted_date
# записываем end_value(максимальное значение), end_date = today
# if predict-date + 1day >= datetime.now()
# если |predicted_value| < current_maximum (предикт сбылася)
# записываем в базу end_value, end_date.
# если нет:
# не делать ничего

# проходимся по всем предиктам (is_active, end_date != None)
# для каждого считаем рейтинг. is_active = false
# делаем рассылку.

async def predictions_active_finished():
    config: Config = load_config()
    #print(config.tg_bot.token)
    bot = Bot(token=config.tg_bot.token, parse_mode='HTML')
    channel_id = config.tg_bot.channel_id
    # await bot.kick_chat_member(chat_id=channel_id, user_id=2065163769, until_date=timedelta(seconds=31))
    # try:
    #     await bot.send_message(chat_id=2065163769, text=f'skljfksdjfksdj')
    # except BotBlocked:
    #     print(f'Bot ЗАБЛОКИРОВАН!!!')
    db_session = await create_db_session(config)
    # список всех предиктов is_active
    predictions: list[Prediction] = await Prediction.get_active_finished_predicts(db_session=db_session)
    for prediction in predictions:
       #print(f' предикт: прогнозируемое значение: {prediction.analytic.__dict__}, {prediction}, {prediction.__dict__}')
        analytic_id = prediction.analytic_id
        analytic = await Analytic.get_analytic_by_id(db_session=db_session, telegram_id=prediction.analytic_id)
        prediction_rating = await prediction.calculate_rating(analytic)
        try:
            if analytic.bonuscount>0:
                bonuscount=analytic.bonuscount-1
                if bonuscount==0:
                    await analytic.update_analytic(db_session=db_session, bonus=0, bonuscount=0)
                else:
                    await analytic.update_analytic(db_session=db_session, bonuscount=bonuscount)
        except TypeError:
            pass


        new_rating = await analytic.calculate_rating(prediction_rating)
        #print(f' ПОСЧИТАННЫЙ РЕЙТИНГ АНАЛИТИКА {new_rating}')

        await Analytic.set_analytic_rating(db_session, rating=new_rating, telegram_id=analytic_id)
        await Prediction.update_predict_rating(db_session, id=prediction.id, rating=prediction_rating)
        updated_prediction = await Prediction.get_predict_by_id(db_session=db_session,
                                                                id=prediction.id)
        #print(f'СТАРЫЙ РЕЙТИНГ {analytic.rating}')
        #print(f' Аалитик: старое: {analytic}, {analytic.__dict__}')
        updated_analytic = await Analytic.get_analytic_by_id(db_session, analytic_id)
        #print(f'НОВЫЙ РЕЙТИНГ АНАЛИТИКА {updated_analytic.rating}')
        rating_delta = updated_analytic.rating - analytic.rating
        #print(f' Аалитик: новое: {updated_analytic}, {updated_analytic.__dict__}')
        # new_text = updated_prediction.message_text

        message_id = updated_prediction.message_id
        message_url = updated_prediction.message_url
        if not message_id: #для старых прогнозов, где в базе нету message_id, message_url и текста
            if prediction.successful:
                text = f'''🚀Прогноз по акции <b>${updated_prediction.ticker}</b> сбылся ⏱<b>{updated_prediction.end_date.date():%d-%m-%Y}</b>. 
🏦Прогноз:<b>{updated_prediction.start_value} {updated_prediction.currency}</b>➡<b>{updated_prediction.end_value} {updated_prediction.currency}</b>
Рейтинг Прогноза: <b>{updated_prediction.rating}</b>
Рейтинг аналитика: <b>{analytic.Nickname}</b>: <b>{analytic.rating}</b>➡<b>{updated_analytic.rating}</b>
Всего прогнозов: <b>{updated_analytic.predicts_total}</b>.'''
            else:
                text = f'''🚫Прогноз по акции <b>${updated_prediction.ticker}</b> не сбылся . 
🏦Прогноз:<b>{updated_prediction.start_value} {updated_prediction.currency}</b>➡<b>{updated_prediction.predicted_value} {updated_prediction.currency}</b>
Фактическое изменение: <b>{updated_prediction.start_value} {updated_prediction.currency}</b>➡<b>{updated_prediction.end_value} {updated_prediction.currency}</b>
Рейтинг прогноза: <b>{updated_prediction.rating}</b>
Рейтинг аналитика <b>{analytic.Nickname}</b>: <b>{analytic.rating}</b>➡<b>{updated_analytic.rating}</b>
Всего прогнозов: <b>{updated_analytic.predicts_total}</b>.'''

            await bot.send_message(chat_id=channel_id,
                                   text=text)

            await bot.send_message(chat_id=channel_id,
                                   text=f'Пульс ${updated_prediction.ticker}',
                                   reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                       [
                                           InlineKeyboardButton(text=f"Open in Tinkoff",
                                                                url=f'https://www.tinkoff.ru/invest/stocks/{updated_prediction.ticker}')
                                       ],
                                   ])
                                   )
        else: #для новых прогнозов с записью в базу ID сообщения, текста и url
            # new_text = new_text.replace("&lt;", "<").replace("&gt;", ">")
            if prediction.successful:
                text_tochannel = f'''🚀Прогноз по акции <b><a href="{message_url}">${updated_prediction.ticker}</a></b> сбылся ⏱<b>{updated_prediction.end_date.date():%d-%m-%Y}</b>. 
🏦Прогноз:<b>{updated_prediction.start_value} {updated_prediction.currency}</b>➡<b>{updated_prediction.end_value} {updated_prediction.currency}</b>
Рейтинг Прогноза: <b>{updated_prediction.rating}</b>
Рейтинг аналитика: <b>{analytic.Nickname}</b>: <b>{analytic.rating}</b>➡<b>{updated_analytic.rating}</b>
Всего прогнозов: <b>{updated_analytic.predicts_total}</b>.'''
            else:
                text_tochannel = f'''❌Прогноз по акции <b><a href="{message_url}">${updated_prediction.ticker}</a></b> не сбылся. 
🏦Прогноз:<b>{updated_prediction.start_value} {updated_prediction.currency}</b>➡<b>{updated_prediction.predicted_value} {updated_prediction.currency}</b>
Фактическое изменение: <b>{updated_prediction.start_value} {updated_prediction.currency}</b>➡<b>{updated_prediction.end_value} {updated_prediction.currency}</b>
Рейтинг прогноза: <b>{updated_prediction.rating}</b>
Рейтинг аналитика <b>{analytic.Nickname}</b>: <b>{analytic.rating}</b>➡<b>{updated_analytic.rating}</b>
Всего прогнозов: <b>{updated_analytic.predicts_total}</b>.'''
                if prediction.stopped:
                    text_tochannel = f'''⛔️СТОП ЛОСС Прогноза по акции <b><a href="{message_url}">${updated_prediction.ticker}</a></b>. 
🏦Прогноз:<b>{updated_prediction.start_value} {updated_prediction.currency}</b>➡<b>{updated_prediction.predicted_value} {updated_prediction.currency}</b>
Фактическое изменение: <b>{updated_prediction.start_value} {updated_prediction.currency}</b>➡<b>{updated_prediction.end_value} {updated_prediction.currency}</b>
Рейтинг прогноза: <b>{updated_prediction.rating}</b>
Рейтинг аналитика <b>{analytic.Nickname}</b>: <b>{analytic.rating}</b>➡<b>{updated_analytic.rating}</b>
Всего прогнозов: <b>{updated_analytic.predicts_total}</b>.'''


            channel_message = await bot.send_message(chat_id=channel_id,
                                   text=text_tochannel)

            await bot.send_message(chat_id=channel_id,
                                   text=f'Пульс ${updated_prediction.ticker}',
                                   reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                       [
                                           InlineKeyboardButton(text=f"Open in Tinkoff",
                                                                url=f'https://www.tinkoff.ru/invest/stocks/{updated_prediction.ticker}')
                                       ],
                                   ])
                                   )

            new_text = await updated_prediction.edit_message_text(db_session=db_session)
            if prediction.successful:
                await bot.edit_message_text(text=new_text + f'\nСтатус: 🚀<b><a href="{channel_message.url}">ЗАВЕРШЕН</a></b>',
                    chat_id=channel_id, message_id=message_id)
            else:
                if prediction.stopped:
                    await bot.edit_message_text(
                        text=new_text + f'\nСтатус: ⛔️<b><a href="{channel_message.url}">СТОП ЛОСС</a></b>',
                        chat_id=channel_id, message_id=message_id)
                else:
                    await bot.edit_message_text(text=new_text + f'\nСтатус: ❌<b><a href="{channel_message.url}">ЗАВЕРШЕН</a></b>',
                    chat_id=channel_id, message_id=message_id)


# noinspection PyTypeChecker
async def prediction_candle_analys(prediction: Prediction, config: Config):
    isLong = math.copysign(1, (prediction.predicted_value - prediction.start_value))
    predict_sign = decimal.Decimal(math.copysign(1, (prediction.predicted_value - prediction.start_value)))
    # #процент АВТОСТОПА
    # autostop_percentage = 15
    # # значение автостопа
    # if isLong:
    #     autostop_value = round(prediction.start_value*decimal.Decimal(1 - autostop_percentage/100),2)
    # else:
    #     autostop_value = round(prediction.start_value*decimal.Decimal(1 + autostop_percentage/100),2)
    #print(prediction.start_date.date() + timedelta(days=2))
    #print(datetime.now().date())
    if prediction.start_date.date() + timedelta(days=2) <= datetime.now().date():
        #print('больше двух дней')

        #print(prediction.start_date + timedelta(hours=2))
        #print(datetime.utcnow())
        #print(isLong)
        candles_lasthour = (
            await get_candles_inrange(figi=prediction.figi, from_=datetime.utcnow()+ timedelta(hours=-2),
                                      to=datetime.utcnow(),
                                      interval='minute',
                                      config=config)).candles

        candles_lasthour = [x for x in candles_lasthour if x.time.replace(tzinfo=None) <= datetime.now()]
        candles_lasthour = [x for x in candles_lasthour if x.time.replace(tzinfo=None) <= prediction.predicted_date]
        candles_firsthour = (
            await get_candles_inrange(figi=prediction.figi, from_=prediction.start_date + timedelta(hours=-1),
                                      to=(prediction.start_date + timedelta(hours=1)).replace(minute=59, second=0),
                                      interval='minute',
                                      config=config)).candles

        candles_firsthour = [x for x in candles_firsthour if x.time.replace(tzinfo=None) >= prediction.start_date]

        candles_hourly = (
            await get_candles_inrange(figi=prediction.figi, from_=prediction.start_date + timedelta(hours=1),
                                      to=prediction.start_date + timedelta(days=2),
                                      interval='hour',
                                      config=config)).candles

        candles_dayly = (
            await get_candles_inrange(figi=prediction.figi,
                                      from_=(prediction.start_date + timedelta(days=1)).replace(hour=23),
                                      to=datetime.now(),
                                      interval='day',
                                      config=config)).candles

        candles_dayly = [x for x in candles_dayly if x.time.replace(tzinfo=None) <= prediction.predicted_date]

        all_candles = candles_firsthour + candles_hourly + candles_dayly + candles_lasthour
        if not all_candles:
            predictionanalysis = None
            return predictionanalysis
        #print(all_candles)
        if isLong > 0:
            bestcandle = max(all_candles, key=lambda item: item.h)
            worstcandle = min(all_candles, key=lambda item: item.l)
            candles_morethen_predicted = [x for x in all_candles if x.h >= prediction.predicted_value]
            # candles_lessthen_autostop = [x for x in all_candles if x.l <= autostop_value]
            try:
                candles_lessthen_stop = [x for x in all_candles if x.l <= prediction.stop_value]
            except TypeError:
                candles_lessthen_stop = []
            #print(f'maxof_candles.h: {bestcandle.h}')
        else:
            bestcandle = min(all_candles, key=lambda item: item.l)
            worstcandle = max(all_candles, key=lambda item: item.h)
            candles_morethen_predicted = [x for x in all_candles if x.l <= prediction.predicted_value]
            # candles_lessthen_autostop = [x for x in all_candles if x.h >= autostop_value]
            try:
                candles_lessthen_stop = [x for x in all_candles if x.h >= prediction.stop_value]
            except:
                candles_lessthen_stop = []
            #print(f'minof_candles_daily.h: {bestcandle.l}')

        # временно убрать!

        # if not candles_morethen_predicted:
        #     predictionanalysis = PredictionAnalys(bestcandle, bestcandle, prediction_index=1)
        #     return predictionanalysis
        try:
            first_candle_morethen_predicted = min(candles_morethen_predicted, key=lambda item: item.time)
        except ValueError:
            first_candle_morethen_predicted = bestcandle
        try:
            first_candle_lessthen_stop = min(candles_lessthen_stop, key=lambda item: item.time)
        except ValueError:
            first_candle_lessthen_stop = worstcandle
        # try:
        #     first_candle_lessthen_autostop = min(candles_lessthen_autostop, key=lambda item: item.time)
        # except ValueError:
        #     first_candle_lessthen_autostop = worstcandle
        #pprint.pprint(f'первая свеча в которых предикт сбылся за всё время : {first_candle_morethen_predicted}')

        if isLong > 0:
            current_difference = prediction.predicted_value - bestcandle.h
            # current_autostop_difference = autostop_value - worstcandle.l
            try:
                current_stop_difference = prediction.stop_value - worstcandle.l
            except TypeError:
                current_stop_difference = -1
        else:
            current_difference = prediction.predicted_value - bestcandle.l
            # current_autostop_difference = autostop_value - worstcandle.h
            try:
                current_stop_difference = prediction.stop_value - worstcandle.h
            except:
                current_stop_difference = 1

        #print(current_difference)
        #print(predict_sign)
        prediction_index = current_difference * predict_sign
        stop_index = current_stop_difference * predict_sign
        # autostop_index = current_autostop_difference * predict_sign
        #print(f'текущая индекс предсказания (сбылся в случае если отрицательное значение): {prediction_index}')
        # выше мы нашли максимальное значение из свечей в двух диапазонах: в первый день почасовые свечи, после этого посуточные свечи. Взяли максимальную из них по значению Candle.h
        #print(prediction.predicted_date.date() + timedelta(days=1))
        predictionAnalys: PredictionAnalys = PredictionAnalys(bestcandle,
                                                              first_candle_morethen_predicted,
                                                              prediction_index,
                                                              worstcandle,
                                                              first_candle_lessthen_stop,
                                                              stop_index)
        return predictionAnalys


    elif prediction.start_date + timedelta(hours=2) <= datetime.utcnow():
        #print(f'от двух часов')
        #print(prediction.start_date + timedelta(hours=2))
        #print(datetime.utcnow())
        # to_time = (prediction.start_date + timedelta(hours=1)).replace(minute=59, second=0)
        # print(to_time)
        #print(isLong)
        candles_firsthour = (
            await get_candles_inrange(figi=prediction.figi, from_=prediction.start_date + timedelta(hours=-1),
                                      to=(prediction.start_date + timedelta(hours=1)).replace(minute=59, second=0),
                                      interval='minute',
                                      config=config)).candles

        candles_firsthour = [x for x in candles_firsthour if x.time.replace(tzinfo=None) >= prediction.start_date]

        candles_lasthour = (
            await get_candles_inrange(figi=prediction.figi, from_=datetime.utcnow() + timedelta(hours=-2),
                                      to=datetime.utcnow(),
                                      interval='minute',
                                      config=config)).candles

        candles_lasthour = [x for x in candles_lasthour if x.time.replace(tzinfo=None) <= datetime.now()]
        candles_lasthour = [x for x in candles_lasthour if x.time.replace(tzinfo=None) <= prediction.predicted_date]


        candles_hourly = (
            await get_candles_inrange(figi=prediction.figi, from_=prediction.start_date, to=datetime.utcnow(),
                                      interval='hour',
                                      config=config)).candles
        #print(f'почасовые№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№№')

        candles_hourly = [x for x in candles_hourly if x.time.replace(tzinfo=None) <= prediction.predicted_date]

        all_candles = candles_firsthour + candles_hourly + candles_lasthour
        if not all_candles:
            predictionanalysis = None
            return predictionanalysis
        #print(all_candles)
        if isLong > 0:
            bestcandle = max(all_candles, key=lambda item: item.h)
            worstcandle = min(all_candles, key=lambda item: item.l)
            candles_morethen_predicted = [x for x in all_candles if x.h >= prediction.predicted_value]
            # candles_lessthen_autostop = [x for x in all_candles if x.l <= autostop_value]
            try:
                candles_lessthen_stop = [x for x in all_candles if x.l <= prediction.stop_value]
            except TypeError:
                candles_lessthen_stop = []
            #print(f'maxof_candles.h: {bestcandle.h}')
        else:
            bestcandle = min(all_candles, key=lambda item: item.l)
            worstcandle = max(all_candles, key=lambda item: item.h)
            candles_morethen_predicted = [x for x in all_candles if x.l <= prediction.predicted_value]
            # candles_lessthen_autostop = [x for x in all_candles if x.h >= autostop_value]
            try:
                candles_lessthen_stop = [x for x in all_candles if x.h >= prediction.stop_value]
            except:
                candles_lessthen_stop = []
            #print(f'minof_candles_daily.h: {bestcandle.l}')

        # временно убрать!

        # if not candles_morethen_predicted:
        #     predictionanalysis = PredictionAnalys(bestcandle, bestcandle, prediction_index=1)
        #     return predictionanalysis
        try:
            first_candle_morethen_predicted = min(candles_morethen_predicted, key=lambda item: item.time)
        except ValueError:
            first_candle_morethen_predicted = bestcandle
        try:
            first_candle_lessthen_stop = min(candles_lessthen_stop, key=lambda item: item.time)
        except ValueError:
            first_candle_lessthen_stop = worstcandle
        # try:
        #     first_candle_lessthen_autostop = min(candles_lessthen_autostop, key=lambda item: item.time)
        # except ValueError:
        #     first_candle_lessthen_autostop = worstcandle

        if isLong > 0:
            current_difference = prediction.predicted_value - bestcandle.h
            # current_autostop_difference = autostop_value - worstcandle.l
            try:
                current_stop_difference = prediction.stop_value - worstcandle.l
            except TypeError:
                current_stop_difference = -1
        else:
            current_difference = prediction.predicted_value - bestcandle.l
            # current_autostop_difference = autostop_value - worstcandle.h
            try:
                current_stop_difference = prediction.stop_value - worstcandle.h
            except:
                current_stop_difference = 1

        #print(current_difference)
        #print(predict_sign)
        prediction_index = current_difference * predict_sign
        stop_index = current_stop_difference * predict_sign
        # autostop_index = current_autostop_difference * predict_sign
        #print(f'текущая индекс предсказания (сбылся в случае если отрицательное значение): {prediction_index}')
        # выше мы нашли максимальное значение из свечей в двух диапазонах: в первый день почасовые свечи, после этого посуточные свечи. Взяли максимальную из них по значению Candle.h
        #print(prediction.predicted_date.date() + timedelta(days=1))
        predictionAnalys: PredictionAnalys = PredictionAnalys(bestcandle,
                                                              first_candle_morethen_predicted,
                                                              prediction_index,
                                                              worstcandle,
                                                              first_candle_lessthen_stop,
                                                              stop_index)
        return predictionAnalys

    else:
        #print('меньше двух часов')
        to_time = (prediction.start_date + timedelta(hours=1)).replace(minute=59, second=0)
        #print(to_time)
        #print(isLong)
        candles_firsthour = (
            await get_candles_inrange(figi=prediction.figi, from_=prediction.start_date + timedelta(hours=-2),
                                      to=datetime.utcnow(), interval='minute',
                                      config=config)).candles
        # if not candles_firsthour:
        #     predictionanalysis = None
        #     return predictionanalysis

        #print(f'dfgkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk')

        candles_firsthour = [x for x in candles_firsthour if x.time.replace(tzinfo=None) >= prediction.start_date]
        candles_firsthour = [x for x in candles_firsthour if x.time.replace(tzinfo=None) <= prediction.predicted_date]

        all_candles = candles_firsthour

        if not all_candles:
            predictionanalysis = None
            return predictionanalysis

        if isLong > 0:
            bestcandle = max(all_candles, key=lambda item: item.h)
            worstcandle = min(all_candles, key=lambda item: item.l)
            candles_morethen_predicted = [x for x in all_candles if x.h >= prediction.predicted_value]
            # candles_lessthen_autostop = [x for x in all_candles if x.l <= autostop_value]
            try:
                candles_lessthen_stop = [x for x in all_candles if x.l <= prediction.stop_value]
            except TypeError:
                candles_lessthen_stop = []
            #print(f'maxof_candles.h: {bestcandle.h}')
        else:
            bestcandle = min(all_candles, key=lambda item: item.l)
            worstcandle = max(all_candles, key=lambda item: item.h)
            candles_morethen_predicted = [x for x in all_candles if x.l <= prediction.predicted_value]
            # candles_lessthen_autostop = [x for x in all_candles if x.h >= autostop_value]
            try:
                candles_lessthen_stop = [x for x in all_candles if x.h >= prediction.stop_value]
            except:
                candles_lessthen_stop = []
            #print(f'minof_candles_daily.h: {bestcandle.l}')

        # временно убрать!

        # if not candles_morethen_predicted:
        #     predictionanalysis = PredictionAnalys(bestcandle, bestcandle, prediction_index=1)
        #     return predictionanalysis
        try:
            first_candle_morethen_predicted = min(candles_morethen_predicted, key=lambda item: item.time)
        except ValueError:
            first_candle_morethen_predicted = bestcandle
        try:
            first_candle_lessthen_stop = min(candles_lessthen_stop, key=lambda item: item.time)
        except ValueError:
            first_candle_lessthen_stop = worstcandle
        # try:
        #     first_candle_lessthen_autostop = min(candles_lessthen_autostop, key=lambda item: item.time)
        # except ValueError:
        #     first_candle_lessthen_autostop = worstcandle

        if isLong > 0:
            current_difference = prediction.predicted_value - bestcandle.h
            # current_autostop_difference = autostop_value - worstcandle.l
            try:
                current_stop_difference = prediction.stop_value - worstcandle.l
            except TypeError:
                current_stop_difference = -1
        else:
            current_difference = prediction.predicted_value - bestcandle.l
            # current_autostop_difference = autostop_value - worstcandle.h
            try:
                current_stop_difference = prediction.stop_value - worstcandle.h
            except:
                current_stop_difference = 1

        #print(current_difference)
        #print(predict_sign)
        prediction_index = current_difference * predict_sign
        stop_index = current_stop_difference * predict_sign
        # autostop_index = current_autostop_difference * predict_sign
        #print(f'текущая индекс предсказания (сбылся в случае если отрицательное значение): {prediction_index}')
        # выше мы нашли максимальное значение из свечей в двух диапазонах: в первый день почасовые свечи, после этого посуточные свечи. Взяли максимальную из них по значению Candle.h
        #print(prediction.predicted_date.date() + timedelta(days=1))
        predictionAnalys: PredictionAnalys = PredictionAnalys(bestcandle,
                                                              first_candle_morethen_predicted,
                                                              prediction_index,
                                                              worstcandle,
                                                              first_candle_lessthen_stop,
                                                              stop_index)
        return predictionAnalys


async def calculate_rating_job():
    await predictions_active()
    await predictions_active_finished()

#
asyncio.run(predictions_active())
asyncio.run(predictions_active_finished())
