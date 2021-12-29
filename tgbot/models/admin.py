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
