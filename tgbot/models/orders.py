import asyncio
from contextlib import suppress
import datetime

from sqlalchemy import Column, BigInteger, Integer, insert, String, ForeignKey, update, func, Boolean, DateTime, \
    MetaData, Numeric, UniqueConstraint
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker, relationship, selectinload

from tgbot.config import load_config
from tgbot.models.users import User
from tgbot.services.database import create_db_session
from tgbot.services.db_base import Base

class Product(Base):
    __tablename__ = "Products"
    id = Column(Integer, primary_key=True, autoincrement="auto")
    title = Column(String(length=100), nullable=False)
    description = Column(String(length=500))
    created_date = Column(DateTime, default=datetime.datetime.utcnow)
    updated_date = Column(DateTime, onupdate=func.now())
    price = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(length=10), default='RUB', nullable=False)
    payload = Column(String(length=50), nullable=False)

    @classmethod
    async def get_product_like_payload(cls,
                                db_session: sessionmaker):
        async with db_session() as db_session:
            sql = select(cls).where(cls.payload.like('%subscription%'))
            request = await db_session.execute(sql)
            prediction: cls = request.scalars()
            return prediction

class PaymentInfo(Base):
    __tablename__ = "PaymentsInfo"
    id = Column(Integer, primary_key=True, autoincrement="auto")
    user_id = Column(BigInteger, ForeignKey(User.telegram_id, ondelete="CASCADE"), nullable=False)
    user = relationship("User", backref="user", lazy="joined")
    email = Column(String(length=100))
    provider = Column(String(length=100), nullable=False)
    provider_payment_charge_id = Column(String(length=200), nullable=False)
    telegram_payment_charge_id = Column(String(length=200), nullable=False)
    invoice_payload = Column(String(length=200), nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(length=10), default='RUB', nullable=False)
    __table_args__ = (UniqueConstraint('provider', 'provider_payment_charge_id', name='_provider_paimentid_uc'),)

    @classmethod
    async def add_paymentinfo(cls,
                          db_session: sessionmaker,
                          user_id: BigInteger,
                          email: str,
                          provider: str,
                          provider_payment_charge_id: str,
                          telegram_payment_charge_id: str,
                          invoice_payload: str,
                          total_amount: Numeric,
                          currency: str
                          ) -> 'PaymentInfo':
        paymentinfo: PaymentInfo = PaymentInfo(user_id=user_id,
                                            email=email,
                                            provider=provider,
                                            provider_payment_charge_id=provider_payment_charge_id,
                                            telegram_payment_charge_id=telegram_payment_charge_id,
                                            invoice_payload=invoice_payload,
                                            total_amount=total_amount,
                                            currency=currency)
        async with db_session() as db_session:
            db_session.add(paymentinfo)
            await db_session.commit()
            return paymentinfo

    @classmethod
    async def get_paymentinfo_by_provider_payment_charge_id(cls,
                          db_session: sessionmaker,
                          provider_payment_charge_id: str) -> 'PaymentInfo':
        async with db_session() as db_session:
            sql = select(cls).where(func.lower(cls.provider_payment_charge_id) == func.lower(provider_payment_charge_id))
            request = await db_session.execute(sql)
            predict: cls = request.scalar()
            return predict




