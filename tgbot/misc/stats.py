import decimal
import math
from datetime import timedelta, datetime

from aiogram import Bot
from sqlalchemy.orm import sessionmaker

from tgbot.models.analytic import Prediction, Analytic

# class Profit_stat():
#     def __init__(self,
#                  best_candle,
#                  first_candle_morethen_predicted,
#                  prediction_index,
#                  worst_candle,
#                  first_candle_lessthen_stop,
#                  stop_index):
#         self.best_candle = best_candle
#         self.first_candle_morethen_predicted = first_candle_morethen_predicted
#         self.prediction_index = prediction_index
#         self.worst_candle = worst_candle
#         self.first_candle_lessthen_stop = first_candle_lessthen_stop
#         self.stop_index = stop_index
#
#     best_candle: Candle
#     first_candle_morethen_predicted: Candle
#     prediction_index: decimal
#     worst_candle: Candle
#     first_candle_lessthen_stop: Candle
#     stop_index: decimal

async def calculate_profit_stat(db_session: sessionmaker):
    db_session = db_session
    await profit_analytics(db_session, 30)
    await profit_analytics(db_session, 90)
    await profit_analytics(db_session, 9999)

    await profit_all(db_session)

async def profit_analytics(db_session: sessionmaker, days: int) -> int:
    analytics = await Analytic.get_all_analytics(db_session=db_session)
    deposit_start_all = 1
    deposit_end_all = deposit_start_all
    for analytic in analytics:
        ### прогнозы за последние 30 дней:
        start_date = datetime.utcnow() + timedelta(days=-days)
        predicts = await Prediction.get_finished_predicts_by_analytic_lastdays(db_session=db_session,
                                                                         analytic_id=analytic.telegram_id,
                                                                         start_date=start_date)
        deposit_start_analytic = deposit_start_all
        deposit_end_analytic = deposit_start_analytic
        predict_deposit_koef = 0.05

        for predict in predicts:
            predicted_value = float(predict.predicted_value)
            start_value = float(predict.start_value)
            end_value = float(predict.end_value)
            print(predict.__dict__)
            predict_sign = (math.copysign(1, (predicted_value - start_value)))
            profit = deposit_start_analytic*predict_deposit_koef*(end_value/start_value -1)*predict_sign
            deposit_end_analytic = deposit_start_analytic + profit

        analytic_profit = deposit_end_analytic-deposit_start_analytic
        analytic_profit_percentage = (deposit_end_analytic-deposit_start_analytic)/deposit_start_analytic
        deposit_end_all += analytic_profit
        all_profit_percentage = (deposit_start_all - deposit_end_all)/deposit_start_all
        print(f'профит за {days} дней:------------------')
        print(f'Аналитик: {analytic.Nickname}')
        print(f'Конечный депозит по аналитику: {deposit_end_analytic}')
        print(f'Профит от Аналитика: {analytic_profit}')
        print(f'Процент профита: {analytic_profit_percentage}')
    print(f'Конечный депозит по всем аналитикам: {deposit_end_all}')
    print(f'Конечный процент профита по всем аналитикам: {all_profit_percentage}')

1) НЕ УЧТЕНО УСРЕДНЕНИЕ!!!
2) ЗАПИСЬ в базу

async def profit_all(db_session: sessionmaker):
    pass