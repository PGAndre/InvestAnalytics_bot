from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from tgbot.config import Config, load_config
from tgbot.services.db_base import Base


async def create_db_session(config: Config):
    engine = create_async_engine(
        f"postgresql+asyncpg://{config.db.user}:{config.db.password}@{config.db.host}/{config.db.database}",
        future=True
    )
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)

    # expire_on_commit=False will prevent attributes from being expired
    # after commit.
    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )
    return async_session

async def get_session() -> AsyncSession:
    config = load_config(".env")
    engine = create_async_engine(
        f"postgresql+asyncpg://{config.db.user}:{config.db.password}@{config.db.host}/{config.db.database}",
        future=True)
    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession)
    return async_session
    # async with async_session() as session:
    #     yield session

