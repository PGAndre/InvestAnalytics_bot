import asyncio
import logging

from aiogram import Bot
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.fsm_storage.redis import RedisStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from tgbot.config import load_config
from tgbot.filters.admin import AdminFilter
from tgbot.filters.analytic import *
from tgbot.handlers.admin import register_admin
from tgbot.handlers.analytic import *
from tgbot.handlers.botuser import register_botuser
from tgbot.handlers.user import register_user
from tgbot.middlewares.db import DbMiddleware
from tgbot.misc.rating import calculate_rating_job
from tgbot.misc.usersmanage import kick_users, notify_users_with_active_sub, notify_users_with_inactive_sub
from tgbot.services.database import create_db_session

logger = logging.getLogger(__name__)


def register_all_middlewares(dp):
    dp.setup_middleware(DbMiddleware())


def register_all_filters(dp):
    dp.filters_factory.bind(AdminFilter)
    dp.filters_factory.bind(AnalyticFilter)


def register_all_handlers(dp):
    register_predict(dp)
    register_admin(dp)
    register_user(dp)
    register_botuser(dp)

   # register_echo(dp)


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format=u'%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s',

    )
    logger.info("Starting bot")
    config = load_config(".env")

    if config.tg_bot.use_redis:
        storage = RedisStorage()
    else:
        storage = MemoryStorage()

    bot = Bot(token=config.tg_bot.token, parse_mode='HTML')
    dp = Dispatcher(bot, storage=storage)

    bot['config'] = config
    bot['db'] = await create_db_session(config)
    scheduler = AsyncIOScheduler()
    print(datetime.now())
    #scheduler.add_job(calculate_rating_job, 'interval', seconds=5)
    scheduler.add_job(calculate_rating_job, "cron", hour='7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23')
    scheduler.add_job(kick_users, "cron", hour='21')
    scheduler.add_job(notify_users_with_active_sub, "cron", hour='20')
    scheduler.add_job(notify_users_with_inactive_sub, 'interval', days=7)

    #register_all_middlewares(dp)
    register_all_filters(dp)
    register_all_handlers(dp)
    scheduler.start()
    # start r4566
    try:
        await dp.start_polling(allowed_updates=["message", "chat_member", "my_chat_member"])
    finally:
        await dp.storage.close()
        await dp.storage.wait_closed()
        await bot.session.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.error("Bot stopped!")
