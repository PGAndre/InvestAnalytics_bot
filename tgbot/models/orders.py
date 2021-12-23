import asyncio
from contextlib import suppress
import datetime

from sqlalchemy import Column, BigInteger, Integer, insert, String, ForeignKey, update, func, Boolean, DateTime, \
    MetaData, Numeric
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker, relationship

from tgbot.config import load_config
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
    currency = Column(Integer, default='RUB', nullable=False)
    payload = Column(String(length=50), nullable=False)
