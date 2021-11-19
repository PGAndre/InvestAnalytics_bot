import asyncio
from logging.handlers import RotatingFileHandler

import aiogram
from aiogram import Bot
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from aiogram.types import BotCommand, BotCommandScope, BotCommandScopeAllPrivateChats, BotCommandScopeType, \
    BotCommandScopeDefault, BotCommandScopeChat
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.combining import OrTrigger
from apscheduler.triggers.cron import CronTrigger

from tgbot.config import load_config
from tgbot.filters.admin import AdminFilter
from tgbot.filters.analytic import *
from tgbot.handlers.admin import register_admin
from tgbot.handlers.analytic import *
from tgbot.handlers.botuser import register_botuser
from tgbot.handlers.channeluser import register_channeluser
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
    register_channeluser(dp)
    register_admin(dp)
    register_analytic(dp)
    register_user(dp)
    register_botuser(dp)

   # register_echo(dp)


async def main():
    handler1 = RotatingFileHandler('/usr/src/app/logs/invest.log', maxBytes=1000000, backupCount=10)
    handler1.lever = logging.ERROR
    handler2 = logging.StreamHandler()
    handler2.level = logging.INFO
    logging.basicConfig(
        level=logging.INFO,
        format=u'%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s',
        handlers=[
            handler1,
            handler2
        ])
    logger.info("Starting bot")
    config = load_config(".env")
    redis_host=config.redis.host
    redis_port = config.redis.port
    redis_password = config.redis.password

    if config.tg_bot.use_redis:
        storage = RedisStorage2(host=redis_host,port=redis_port,password=redis_password)
    else:
        storage = MemoryStorage()

    bot = Bot(token=config.tg_bot.token, parse_mode='HTML')
    dp = Dispatcher(bot, storage=storage)

    # scope = BotCommandScopeDefault(type=BotCommandScopeType.DEFAULT)
    # await bot.set_my_commands(commands=command, scope=scope)

    # scope = BotCommandScopeChat(chat_id=-1001317811501)


    command = [BotCommand("menu", "открыть меню")]
    scope = BotCommandScopeAllPrivateChats(type=BotCommandScopeType.ALL_PRIVATE_CHATS) # именять команды только к приватным чатам
    await bot.delete_my_commands(scope=scope) #удаляем меню из ранее установленных чатов
    await bot.delete_my_commands() # удаляем меню изо всех других чатов, куда он прилетал.
    await bot.set_my_commands(commands=command, scope=scope) #устанавливаем меню в private chats

    bot['config'] = config
    bot['db'] = await create_db_session(config)
    scheduler = AsyncIOScheduler()
    print(datetime.now())
    #scheduler.add_job(calculate_rating_job, 'interval', seconds=5)
    trigger = OrTrigger([
        CronTrigger(hour='0-23', minute='*'),
    ])
    scheduler.add_job(calculate_rating_job, trigger)
    # scheduler.add_job(calculate_rating_job, "cron", hour='7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23')
    scheduler.add_job(kick_users, "cron", hour='18')
    scheduler.add_job(notify_users_with_active_sub, "cron", hour='17')
    scheduler.add_job(notify_users_with_inactive_sub, "cron", hour='17')
    #scheduler.add_job(kick_users, 'interval', seconds=5)

    #register_all_middlewares(dp)
    register_all_filters(dp)
    register_all_handlers(dp)
    scheduler.start()
    # start r4566
    try:
        await dp.start_polling(allowed_updates=["message", "chat_member", "my_chat_member", "callback_query", "pre_checkout_query", "successful_payment"])
    finally:
        await dp.storage.close()
        await dp.storage.wait_closed()
        await bot.session.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.error("Bot stopped!")
