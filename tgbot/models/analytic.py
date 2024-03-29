import asyncio
import datetime
import decimal
import logging
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
    async def get_analytics(cls, db_session: sessionmaker, active: bool):
        async with db_session() as db_session:
            sql = select(cls).where(cls.is_active == active)
            request = await db_session.execute(sql)
            analytic: cls = request.scalars().all()
            return analytic

    @classmethod
    async def get_all_analytics(cls, db_session: sessionmaker):
        async with db_session() as db_session:
            sql = select(cls)
            request = await db_session.execute(sql)
            analytic: cls = request.scalars().all()
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
                                  rating: Integer, ):
        async with db_session() as db_session:
            sql = update(cls).where(cls.telegram_id == telegram_id).values(rating=rating,
                                                                           predicts_total=cls.predicts_total + 1)
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

        new_rating = (float(predicts_total * rating) + k * last_rating) / (predicts_total + k)
        print(new_rating)
        rounded_rating = round(new_rating, 2)
        return rounded_rating

    async def update_analytic(self, db_session: sessionmaker, **updated_fields: dict) -> 'Analytic':
        async with db_session() as db_session:
            sql = update(Analytic).where(Analytic.telegram_id == self.telegram_id).values(**updated_fields).returning(
                '*')
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
    stop_value = Column(Numeric(12, 2), nullable=True)
    end_value = Column(Numeric(12, 2))
    analytic_id = Column(BigInteger, ForeignKey(Analytic.telegram_id, ondelete="CASCADE"), nullable=False)
    rating = Column(Numeric(4, 2))
    updated_date = Column(DateTime, onupdate=func.now())
    is_active = Column(Boolean, default=True, nullable=False)
    analytic = relationship("Analytic", backref="analytic", lazy="joined")
    successful = Column(Boolean, default=False)
    stopped = Column(Boolean, default=False, nullable=True)
    message_id = Column(BigInteger, nullable=True)
    message_url = Column(String(100), nullable=True)
    message_text = Column(String(2000), nullable=True)
    comment = Column(String(4000), nullable=True)
    risk_level = Column(Integer, nullable=True)

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
                          message_text: str,
                          comment: str,
                          risk_level: Integer,
                          stop_value: Numeric

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
                                            message_text=message_text,
                                            comment=comment,
                                            risk_level=risk_level,
                                            stop_value=stop_value)
        async with db_session() as db_session:
            db_session.add(prediction)
            await db_session.commit()
            return prediction

    @classmethod
    async def get_predict(cls,
                          db_session: sessionmaker,
                          ticker: str) -> 'Prediction':
        async with db_session() as db_session:
            sql = select(cls).where(func.lower(cls.ticker) == func.lower(ticker)).where(cls.is_active == true()).join(
                Analytic,
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
            sql = select(cls).where(cls.is_active == true()).where(cls.analytic_id == analytic_id).where(
                func.lower(cls.ticker) == func.lower(ticker)).join(Analytic,
                                                                   Analytic.telegram_id == cls.analytic_id)
            request = await db_session.execute(sql)
            predict: cls = request.scalar()
            return predict

    @classmethod
    async def get_predict_by_analytic(cls,
                                      db_session: sessionmaker,
                                      analytic_id: BigInteger) -> 'Prediction':
        async with db_session() as db_session:
            sql = select(cls).where(cls.is_active == true()).where(cls.analytic_id == analytic_id).join(Analytic,
                                                                                                        Analytic.telegram_id == cls.analytic_id)
            request = await db_session.execute(sql)
            predict: cls = request.scalars()
            return predict

    @classmethod
    async def get_finished_predicts_by_analytic_lastdays(cls,
                                                         db_session: sessionmaker,
                                                         analytic_id: BigInteger,
                                                         start_date: datetime) -> 'Prediction':
        async with db_session() as db_session:
            sql = select(cls).where(cls.is_active != true()).where(cls.analytic_id == analytic_id).where(
                cls.end_date >= start_date).join(Analytic,
                                                 Analytic.telegram_id == cls.analytic_id).join(Prediction_averaging,
                                                                                               Prediction_averaging.prediction_id == cls.id,
                                                                                               isouter=True)
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
                             successful: Boolean,
                             end_value: Numeric,
                             end_date: datetime,
                             id: int,
                             **updated_fields):
        async with db_session() as db_session:
            sql = update(cls).where(cls.id == id).values(successful=successful, end_date=end_date, end_value=end_value,
                                                         **updated_fields)
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

    async def calculate_rating(self, db_session: sessionmaker, analytic):
        prediction_averaging = await Prediction_averaging.get_averaging_by_predict(db_session=db_session,
                                                                                   prediction_id=self.id)

        logger = logging.getLogger(__name__)
        end_value = self.end_value
        predicted_value = self.predicted_value
        start_value = self.start_value

        if prediction_averaging is not None:
            start_value = prediction_averaging.averaging_value
            predicted_value = prediction_averaging.predicted_value
        start_date = self.start_date
        predicted_date = self.predicted_date
        end_date = self.end_date
        predict_days = (end_date.date() - start_date.date()).days
        predict_days = await bdays.count_tdays(start_date, end_date)
        bonus = 0
        risk_level = self.risk_level
        try:
            if analytic.bonuscount > 0:
                bonus = analytic.bonus
        except TypeError:
            pass

        # print(f'predicted_days: {predict_days}')
        # print(f'end_value: {end_value} !!!!  predicted_value: {predicted_value} !!!! start:value: {start_value} !!!!!'
        #       f' start date: {start_date} !!!!! predicted_date: {predicted_date} !!!!! end_date: {end_date}')

        isLong = math.copysign(1, (predicted_value - start_value))
        profit = (end_value - start_value) * Decimal(isLong) / start_value
        predicted_profit = (predicted_value - start_value) * Decimal(isLong) / start_value
        # print(f'PREDICTED PROFIT: {predicted_profit}')
        sign_profit = math.copysign(1, profit)
        # print(f'SIGN_PROFIT: {sign_profit}')
        # print(f'PROFIT: {profit}')
        # print(current_difference)
        # predict_sign = decimal.Decimal(math.copysign(1, (prediction.predicted_value - prediction.start_value)))
        # print(predict_sign)
        # prediction_index = current_difference * predict_sign
        # bonus=random.randrange(bonus*100-20,bonus*100+20,1)/100
        predict_days = min(predict_days, 21)
        delta = sign_profit * math.pow((min((22 - predict_days), 22) / 22), 1 / 3) * math.pow(
            float(predicted_profit) / 0.30, 1 / 3) * math.pow(min(abs(profit), predicted_profit) / predicted_profit,
                                                              1 / 3)
        rating = (1 + delta) / 2
        ##бонсуы за РИСКИ

        risk_bonus = 0.8
        if risk_level == 1:
            if rating < 0.5:
                rating = rating * risk_bonus
                logger.info(f'{self.ticker}, rating = rating*risk_bonus, risk_level == 1:')
            elif rating > 0.5:
                rating = 1 - ((1 - rating) * risk_bonus)
                logger.info(f'{self.ticker}, rating = 1 - ((1-rating)*risk_bonus), risk_level == 1:')
            else:
                logger.info(f'{self.ticker}, рейтинг = 50')

        elif risk_level == 3:
            if rating < 0.5:
                rating = rating + (0.5 - rating) * (1 - risk_bonus)
                logger.info(f'{self.ticker}, rating = rating + (0.5 - rating)*(1-risk_bonus), risk_level == 3:')
            elif rating > 0.5:
                rating = 0.5 + (rating - 0.5) * risk_bonus
                logger.info(f'{self.ticker}, rating = 0.5 + (rating-0.5)*risk_bonus, risk_level == 3:')
            else:
                logger.info(f'{self.ticker}, рейтинг = 50')
        elif risk_level == 2:
            logger.info(f'{self.ticker}, risk_level == 2:')

        # бонус ИНТРАДЕЙ
        intraday_bonus = 0.8
        if predict_days < 2:
            if rating > 0.5:
                rating = 1 - ((1 - rating) * intraday_bonus)
                logger.info(f'ИНТРАДЕЙ БОНУС для прогноза {self.ticker}')
        #        rating = (31 - predict_days)/30
        rating_rounded = round(rating * 100, 2)
        overbonus = random.randrange(180, 220, 1) / 100
        if sign_profit > 0:
            rating_rounded += bonus
            if rating_rounded > 100:
                rating_rounded = 100 - overbonus
        else:
            rating_rounded += bonus
            if rating_rounded > 50:
                rating_rounded = 50 - overbonus
        rating_rounded = round(rating_rounded, 2)
        if start_value == end_value:
            logger.info(f'ЦЕНА не изменилась в прогнозе {self.ticker}')
            rating_rounded = 50
        # print(math.pow(min((22 - predict_days), 22)/22, 1/3))
        # print(math.pow(float(predicted_profit)/0.30, 1/3))
        # print(math.pow(min(abs(profit), predicted_profit)/predicted_profit, 1/3))
        # print(f'RATING: {rating_rounded}')
        return rating_rounded

    async def edit_message_text(self,
                                db_session: sessionmaker) -> str:
        message_text = self.message_text
        message_text = message_text.replace("&lt;", "<").replace("&gt;", ">")
        comments_raw = await Prediction_comment.get_comments_by_predict(db_session=db_session,
                                                                        prediction_id=self.id)
        comments = []
        for comment in comments_raw:
            comments.append(comment)

        if not comments:
            pass
        else:
            comments.sort(key=lambda r: r.created_date)
            comment_texts = []
            message_text = message_text + '\nКоментарии от аналитика:'
            for comment in comments:
                comment_text = comment.comment[0:25] + '...'
                # text = f'\n<b><a href = "{comment.message_url}">Коментарий от {comment.created_date:%d-%m-%Y %H:%M}</a></b>'
                text = f'\n<b><a href = "{comment.message_url}">{comment_text}</a></b>'
                message_text = message_text + text
                comment_texts.append(comment.comment)

        prediction_averaging = await Prediction_averaging.get_averaging_by_predict(db_session=db_session,
                                                                                   prediction_id=self.id)

        if prediction_averaging is not None:
            averaging_value = prediction_averaging.start_value
            averaging_text_link = f'''Усреднение на {averaging_value} {self.currency}:'''
            averaging_text = f'''💲Новая цель прогноза: <b>{prediction_averaging.predicted_value} {self.currency}</b>
⛔Новый СТОП ЛОСС: <b>{prediction_averaging.stop_value} {self.currency}</b>'''
            # text = f'\n<b><a href = "{comment.message_url}">Коментарий от {comment.created_date:%d-%m-%Y %H:%M}</a></b>'
            text = f'\n<b><a href = "{prediction_averaging.message_url}">{averaging_text_link}</a></b>\n' + averaging_text
            message_text = message_text + text
        return message_text


class Prediction_comment(Base):
    __tablename__ = 'Predicts_comments'

    id = Column(Integer, primary_key=True, autoincrement="auto")
    prediction_id = Column(BigInteger, ForeignKey(Prediction.id, ondelete="CASCADE"), nullable=False)
    comment = Column(String(4000), nullable=True)
    predict = relationship("Prediction", backref="predict", lazy="joined")
    created_date = Column(DateTime, default=datetime.datetime.utcnow)
    updated_date = Column(DateTime(timezone=True), onupdate=func.now())
    message_id = Column(BigInteger, nullable=True)
    message_url = Column(String(100), nullable=True)

    @classmethod
    async def get_comments_by_predict(cls,
                                      db_session: sessionmaker,
                                      prediction_id: BigInteger):
        async with db_session() as db_session:
            sql = select(cls).where(cls.prediction_id == prediction_id)
            request = await db_session.execute(sql)
            predict: cls = request.scalars()
            return predict

    @classmethod
    async def add_prediction_comment(cls,
                                     db_session: sessionmaker,
                                     prediction_id: BigInteger,
                                     comment: str,
                                     message_id: BigInteger,
                                     message_url: str
                                     ) -> 'Prediction':
        prediction_comment: Prediction_comment = Prediction_comment(prediction_id=prediction_id,
                                                                    comment=comment,
                                                                    message_id=message_id,
                                                                    message_url=message_url
                                                                    )
        async with db_session() as db_session:
            db_session.add(prediction_comment)
            await db_session.commit()
            return prediction_comment
        # E = (1 + sign(r) * power((D - d) / (D - 1), 1 / 3) * power(p / P, 1 / 3) * power(min( | r |, p) / p, 1 / 3)) / 2


class Prediction_averaging(Base):
    __tablename__ = 'Predicts_averaging'

    id = Column(Integer, primary_key=True, autoincrement="auto")
    prediction_id = Column(BigInteger, ForeignKey(Prediction.id, ondelete="CASCADE"), nullable=False)
    predicted_date = Column(DateTime, nullable=False)
    start_value = Column(Numeric(12, 2))
    averaging_value = Column(Numeric(12, 2), nullable=False)
    predicted_value = Column(Numeric(12, 2), nullable=False)
    stop_value = Column(Numeric(12, 2), nullable=True)
    message_id = Column(BigInteger, nullable=True)
    message_url = Column(String(100), nullable=True)
    created_date = Column(DateTime, default=datetime.datetime.utcnow)
    updated_date = Column(DateTime(timezone=True), onupdate=func.now())

    @classmethod
    async def get_averaging_by_predict(cls,
                                       db_session: sessionmaker,
                                       prediction_id: BigInteger):
        async with db_session() as db_session:
            sql = select(cls).where(cls.prediction_id == prediction_id)
            request = await db_session.execute(sql)
            predict_averaging: cls = request.scalar()
            return predict_averaging

    @classmethod
    async def add_prediction_averaging(cls,
                                       db_session: sessionmaker,
                                       prediction_id: BigInteger,
                                       predicted_date: datetime,
                                       averaging_value: Numeric,
                                       start_value: Numeric,
                                       predicted_value: Numeric,
                                       stop_value: Numeric,
                                       message_id: BigInteger,
                                       message_url: str
                                       ) -> 'Prediction_averaging':
        prediction_averaging: Prediction_averaging = Prediction_averaging(prediction_id=prediction_id,
                                                                          predicted_date=predicted_date,
                                                                          averaging_value=averaging_value,
                                                                          start_value=start_value,
                                                                          predicted_value=predicted_value,
                                                                          stop_value=stop_value,
                                                                          message_id=message_id,
                                                                          message_url=message_url

                                                                          )
        async with db_session() as db_session:
            db_session.add(prediction_averaging)
            await db_session.commit()
            return prediction_averaging
