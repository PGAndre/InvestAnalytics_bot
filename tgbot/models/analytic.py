import asyncio
import datetime
import decimal
import math
from contextlib import suppress
from decimal import Decimal
import random

from sqlalchemy import Column, BigInteger, Integer, insert, String, ForeignKey, update, func, DateTime, Sequence, \
    Numeric, Boolean, true, MetaData
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker, relationship

from tgbot.config import load_config
from tgbot.misc import bdays
from tgbot.services.database import create_db_session
from tgbot.services.db_base import Base


class Analytic(Base):
    __tablename__ = 'Analytics'
    Nickname = Column(String(100))
    description = Column(String(500), nullable=True)
    telegram_id = Column(BigInteger, primary_key=True, nullable=False)
    predicts_total = Column(Integer, default=0, nullable=False)
    rating = Column(Numeric(4, 2), default=50.00, nullable=False)
    created_date = Column(DateTime, default=datetime.datetime.utcnow)
    updated_date = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    bonus = Column(Integer, default=0, nullable=True)
    bonuscount = Column(Integer, default=0, nullable=True)


    @classmethod
    async def get_analytics(cls, db_session:sessionmaker, active:bool):
        async with db_session() as db_session:
            sql = select(cls).where(cls.is_active == active)
            request = await db_session.execute(sql)
            analytic: cls = request.scalars()
            return analytic


    @classmethod
    async def add_analytic(cls,
                          db_session: sessionmaker,
                          telegram_id: BigInteger,
                          nickname: str) -> 'Analytic':
        analytic: Analytic = Analytic(telegram_id=telegram_id, Nickname=nickname)
        async with db_session() as db_session:
            db_session.add(analytic)
            await db_session.commit()
            return analytic

    @classmethod
    async def set_analytic_rating(cls,
                        db_session: sessionmaker,
                        telegram_id: BigInteger,
                        rating: Integer,):
        async with db_session() as db_session:
            sql = update(cls).where(cls.telegram_id == telegram_id).values(rating=rating, predicts_total=cls.predicts_total+1)
            await db_session.execute(sql)
            await db_session.commit()

    @classmethod
    async def get_analytic_by_id(cls,
                                db_session: sessionmaker,
                                telegram_id: BigInteger):
        async with db_session() as db_session:
            sql = select(cls).where(cls.telegram_id == telegram_id)
            request = await db_session.execute(sql)
            analytic: cls = request.scalar()
            return analytic


    async def calculate_rating(self, last_rating: float):
        k = 1.3
        predicts_total = self.predicts_total
        rating = self.rating

        new_rating = (float(predicts_total*rating) + k*last_rating)/(predicts_total + k)
        print(new_rating)
        rounded_rating = round(new_rating,2)
        return rounded_rating

    async def update_analytic(self, db_session: sessionmaker, **updated_fields: dict) -> 'Analytic':
        async with db_session() as db_session:
            sql = update(Analytic).where(Analytic.telegram_id == self.telegram_id).values(**updated_fields).returning('*')
            result = await db_session.execute(sql)
            await db_session.commit()
            return result.first()




class Prediction(Base):
    __tablename__ = 'Predicts'

    id = Column(Integer, primary_key=True, autoincrement="auto")
    ticker = Column(String(10), nullable=False)
    name = Column(String(100), nullable=False)
    currency = Column(String(10), nullable=False)
    figi = Column(String(30), nullable=False)
    start_date = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    predicted_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime)
    start_value = Column(Numeric(12, 2))
    predicted_value = Column(Numeric(12, 2), nullable=False)
    end_value = Column(Numeric(12, 2))
    analytic_id = Column(BigInteger, ForeignKey(Analytic.telegram_id, ondelete="CASCADE"), nullable=False)
    rating = Column(Numeric(4, 2))
    updated_date = Column(DateTime, onupdate=func.now())
    is_active = Column(Boolean, default=True, nullable=False)
    analytic = relationship("Analytic", backref="analytic", lazy="joined")
    successful = Column(Boolean, default=False)
    message_id = Column(BigInteger, nullable=True)
    message_url = Column(String(100), nullable=True)
    message_text = Column(String(2000), nullable=True)

    @classmethod
    async def add_predict(cls,
                          db_session: sessionmaker,
                          ticker: str,
                          name: str,
                          currency: str,
                          figi: str,
                          predicted_date: datetime,
                          start_value: Numeric,
                          predicted_value: Numeric,
                          analytic_id: BigInteger,
                          message_id: BigInteger,
                          message_url: str,
                          message_text: str
                          ) -> 'Prediction':
        prediction: Prediction = Prediction(ticker=ticker,
                                            name=name,
                                            currency=currency,
                                            figi=figi,
                                            predicted_date=predicted_date,
                                            start_value=start_value,
                                            predicted_value=predicted_value,
                                            analytic_id=analytic_id,
                                            message_id=message_id,
                                            message_url=message_url,
                                            message_text=message_text)
        async with db_session() as db_session:
            db_session.add(prediction)
            await db_session.commit()
            return prediction

    @classmethod
    async def get_predict(cls,
                          db_session: sessionmaker,
                          ticker: str) -> 'Prediction':
        async with db_session() as db_session:
            sql = select(cls).where(func.lower(cls.ticker) == func.lower(ticker)).where(cls.is_active == true()).join(Analytic,
                                                                                       Analytic.telegram_id == cls.analytic_id)
            request = await db_session.execute(sql)
            predict: cls = request.scalar()
            return predict

    @classmethod
    async def get_predict_analytic_ticker(cls,
                          db_session: sessionmaker,
                          ticker: str,
                        analytic_id: BigInteger) -> 'Prediction':
        async with db_session() as db_session:
            sql = select(cls).where(cls.is_active == true()).where(cls.analytic_id == analytic_id).where(func.lower(cls.ticker) == func.lower(ticker)).join(Analytic,
                                                                                       Analytic.telegram_id == cls.analytic_id)
            request = await db_session.execute(sql)
            predict: cls = request.scalar()
            return predict

    @classmethod
    async def get_predict_by_analytic(cls,
                          db_session: sessionmaker,
                          analytic_id: BigInteger ) -> 'Prediction':
        async with db_session() as db_session:
            sql = select(cls).where(cls.is_active == true()).where(cls.analytic_id == analytic_id).join(Analytic,
                                                                                       Analytic.telegram_id == cls.analytic_id)
            request = await db_session.execute(sql)
            predict: cls = request.scalars()
            return predict

    # @classmethod
    # async def get_predict(cls,
    #                       db_session: sessionmaker,
    #                       ticker: str,
    #                       telegram_id: BigInteger) -> 'Prediction':
    #     async with db_session() as db_session:
    #         sql = select(cls).where(func.lower(cls.ticker) == func.lower(ticker)).where(cls.is_active == true()).join(Analytic,
    #                                                                                    Analytic.telegram_id == telegram_id)
    #         request = await db_session.execute(sql)
    #         predict: cls = request.scalar()
    #         return predict

    # функция возвращает активных list[Prediction]
    @classmethod
    async def get_active_predicts(cls, db_session: sessionmaker):
        async with db_session() as db_session:
            # sql = select(cls).where([(cls.is_active == true()), (cls.end_date == None)])
            sql = select(cls).where(cls.is_active == true()).where(cls.end_date == None)
            request = await db_session.execute(sql)
            predictions: list[Prediction] = request.scalars()
            return predictions

    @classmethod
    async def get_active_finished_predicts(cls, db_session: sessionmaker):
        async with db_session() as db_session:
            # sql = select(cls).where([(cls.is_active == true()), (cls.end_date == None)])
            sql = select(cls).where(cls.is_active == true()).where(cls.end_date != None)
            request = await db_session.execute(sql)
            predictions: list[Prediction] = request.scalars()
            return predictions

    @classmethod
    async def update_predict(cls, db_session: sessionmaker,
                             successful :Boolean,
                             end_value: Numeric,
                             end_date: datetime,
                             id: int):
        async with db_session() as db_session:
            sql = update(cls).where(cls.id == id).values(successful=successful, end_date=end_date, end_value=end_value)
            await db_session.execute(sql)
            await db_session.commit()


    @classmethod
    async def update_predict_rating(cls, db_session: sessionmaker,
                             rating: Integer,
                             id: int) -> 'Prediction':
        async with db_session() as db_session:
            sql = update(cls).where(cls.id == id).values(is_active=False, rating=rating).returning(cls)
            request = await db_session.execute(sql)
            predictions = request.all()
            await db_session.commit()
        return predictions

    @classmethod
    async def get_predict_by_id(cls,
                                db_session: sessionmaker,
                                id: int):
        async with db_session() as db_session:
            sql = select(cls).where(cls.id == id)
            request = await db_session.execute(sql)
            prediction: cls = request.scalar()
            return prediction


    async def calculate_rating(self, analytic):
        end_value = self.end_value
        predicted_value = self.predicted_value
        start_value = self.start_value
        start_date = self.start_date
        predicted_date = self.predicted_date
        end_date = self.end_date
        predict_days = (end_date.date() - start_date.date()).days
        predict_days = await bdays.count_tdays(start_date, end_date)
        bonus=0
        try:
            if analytic.bonuscount > 0:
                bonus=analytic.bonus
        except TypeError:
            pass


        print(f'predicted_days: {predict_days}')
        print(f'end_value: {end_value} !!!!  predicted_value: {predicted_value} !!!! start:value: {start_value} !!!!!'
              f' start date: {start_date} !!!!! predicted_date: {predicted_date} !!!!! end_date: {end_date}')

        isLong = math.copysign(1, (predicted_value - start_value))
        profit = (end_value - start_value)*Decimal(isLong)/start_value
        predicted_profit = (predicted_value - start_value)*Decimal(isLong)/start_value
        print(f'PREDICTED PROFIT: {predicted_profit}')
        sign_profit = math.copysign(1, profit)
        print(f'SIGN_PROFIT: {sign_profit}')
        print(f'PROFIT: {profit}')
        # print(current_difference)
        # predict_sign = decimal.Decimal(math.copysign(1, (prediction.predicted_value - prediction.start_value)))
        # print(predict_sign)
        # prediction_index = current_difference * predict_sign
        bonus=random.randrange(bonus*100-20,bonus*100+20,1)/100
        delta=sign_profit*math.pow((min((22 - predict_days), 22)/22), 1/3)*math.pow(float(predicted_profit)/0.30, 1/3)*math.pow(min(abs(profit), predicted_profit)/predicted_profit, 1/3)
        rating = (1 + delta)/2
#        rating = (31 - predict_days)/30
        rating_rounded = round(rating*100, 2)
        overbonus=random.randrange(180,220,1)/100
        if sign_profit > 0:
            rating_rounded += bonus
            if rating_rounded > 100:
                rating_rounded = 100 - overbonus
        else:
            rating_rounded += bonus
            if rating_rounded > 50:
                rating_rounded = 50-overbonus
        rating_rounded = round(rating_rounded,2)
        print(math.pow(min((22 - predict_days), 22)/22, 1/3))
        print(math.pow(float(predicted_profit)/0.30, 1/3))
        print(math.pow(min(abs(profit), predicted_profit)/predicted_profit, 1/3))
        print(f'RATING: {rating_rounded}')
        return rating_rounded



        #E = (1 + sign(r) * power((D - d) / (D - 1), 1 / 3) * power(p / P, 1 / 3) * power(min( | r |, p) / p, 1 / 3)) / 2



