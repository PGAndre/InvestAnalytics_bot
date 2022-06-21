from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import redis.asyncio as redis

from tgbot.config import load_config
from tgbot.services.database import create_db_session

# Dependency
# async def get_session() -> AsyncSession:
#     config = load_config(".env")
#     async with create_db_session(config=config) as session:
#         yield session

async def get_redis_client():
    config = load_config(".env")
    async with redis.Redis(host=config.redis.host, port=config.redis.port, password=config.redis.password) as redis_client:
        yield redis_client
    # return redis_client