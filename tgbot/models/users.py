import asyncio
from contextlib import suppress
import datetime

from sqlalchemy import Column, BigInteger, insert, String, ForeignKey, update, func, Boolean, DateTime, MetaData
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker, relationship

from tgbot.config import load_config
from tgbot.services.database import create_db_session
from tgbot.services.db_base import Base


class User(Base):
    __tablename__ = "Users"
    telegram_id = Column(BigInteger, primary_key=True)
    first_name = Column(String(length=100))
    last_name = Column(String(length=100), nullable=True)
    username = Column(String(length=100), nullable=True)
    role = Column(String(length=100), default='user')
    subscription_until = Column(DateTime, default=datetime.datetime.utcnow)
    created_date = Column(DateTime, default=datetime.datetime.utcnow)
    updated_date = Column(DateTime, onupdate=func.now())
    is_member = Column(Boolean, default=True)
    is_botuser = Column(Boolean, default=False)

    @classmethod
    async def get_user(cls, db_session: sessionmaker, telegram_id: int) -> 'User':
        async with db_session() as db_session:
            sql = select(cls).where(cls.telegram_id == telegram_id)
            request = await db_session.execute(sql)
            user: cls = request.scalar()
        return user


    @classmethod
    async def get_users_sub(cls, db_session: sessionmaker,
                            time: datetime,
                            is_member: bool) -> 'list[User]':
        async with db_session() as db_session:
            sql = select(cls).where(cls.role == 'user').where(cls.is_member == is_member).where(cls.subscription_until < time)
            request = await db_session.execute(sql)
            users: list[cls] = request.scalars()
        return users




    @classmethod
    async def add_user(cls,
                       db_session: sessionmaker,
                       subscription_until: datetime,
                       telegram_id: int,
                       first_name: str = None,
                       last_name: str = None,
                       username: str = None,
                       **optional_fields: dict,
                       ) -> 'User':
        async with db_session() as db_session:
            sql = insert(cls).values(subscription_until=subscription_until,
                                     telegram_id=telegram_id,
                                     first_name=first_name,
                                     last_name=last_name,
                                     username=username,
                                     **optional_fields).returning('*')
            result = await db_session.execute(sql)
            await db_session.commit()
            return result.first()

    async def update_user(self, db_session: sessionmaker, **updated_fields: dict) -> 'User':
        async with db_session() as db_session:
            sql = update(User).where(User.telegram_id == self.telegram_id).values(**updated_fields).returning('*')
            result = await db_session.execute(sql)
            await db_session.commit()
            return result.first()


if __name__ == '__main__':
    from faker import Faker
    import sqlalchemy.exc


    async def test():

        fake = Faker()
        Faker.seed(0)

        config = load_config()
        session = await create_db_session(config)

        ids = [num for num in range(1, 101)]
        names = [fake.first_name() for _ in range(1, 101)]

        for user_id, first_name in zip(ids, names):
            with suppress(sqlalchemy.exc.IntegrityError):
                user = await User.add_user(session, user_id, first_name)
                # user = await User.get_user(session, user_id)
                print(user)

                referrer = user

                if referrer:
                    await Referral.add_user(session, user_id, referrer.telegram_id)

                refs = await User.count_referrals(session, user)
                print(refs)


    asyncio.run(test())
