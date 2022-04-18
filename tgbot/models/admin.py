import asyncio
from contextlib import suppress
import datetime

from sqlalchemy import Column, BigInteger, Integer, insert, String, ForeignKey, update, func, Boolean, DateTime, \
    MetaData, Numeric, UniqueConstraint, Date, Time, true
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker, relationship, selectinload

from tgbot.config import load_config
from tgbot.services.database import create_db_session
from tgbot.services.db_base import Base

class Document(Base):
    __tablename__ = "Documents"
    id = Column(Integer, primary_key=True, autoincrement="auto")
    title = Column(String(length=100), nullable=True)
    file_name = Column(String(length=500), nullable=False)
    file_id = Column(String(length=500), nullable=False)
    created_date = Column(DateTime, default=datetime.datetime.utcnow)
    updated_date = Column(DateTime, onupdate=func.now())

    @classmethod
    async def get_document_by_title(cls,
                          db_session: sessionmaker,
                          title: str) -> 'Document':
        async with db_session() as db_session:
            sql = select(cls).where(func.lower(cls.title) == func.lower(title))
            request = await db_session.execute(sql)
            document: cls = request.scalar()
            return document

class Message(Base):
    __tablename__ = "Messages"
    id = Column(Integer, primary_key=True, autoincrement="auto")
    title = Column(String(length=100), nullable=False)
    created_date = Column(DateTime, default=datetime.datetime.utcnow)
    updated_date = Column(DateTime, onupdate=func.now())
    message = Column(String(4000), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    type = Column(String(50), nullable=False)
    message_date = Column(Date, nullable=True)
    message_time = Column(Time, nullable=True)
    recipients_query = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_sent_date = Column(DateTime, nullable=True)


    @classmethod
    async def get_active_messages(cls, db_session:sessionmaker):
        async with db_session() as db_session:
            sql = select(cls).where(cls.is_active == true())
            request = await db_session.execute(sql)
            messages: cls = request.scalars()
            return messages

    async def update_message(self, db_session: sessionmaker, **updated_fields: dict) -> 'Message':
        async with db_session() as db_session:
            sql = update(Message).where(Message.id == self.id).values(**updated_fields).returning('*')
            result = await db_session.execute(sql)
            await db_session.commit()
            return result.first()

