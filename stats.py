import asyncio
import logging
from logging.handlers import RotatingFileHandler

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from tgbot.config import load_config
from tgbot.misc.stats import *
from tgbot.services.database import create_db_session

logger = logging.getLogger(__name__)


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
    logger.info("Starting Stats")
    config = load_config(".env")
    db_session = await create_db_session(config)
    scheduler = AsyncIOScheduler()
    scheduler.add_job(calculate_profit_stat, "cron", [db_session], hour='10')
    scheduler.start()
    await calculate_profit_stat(db_session)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.error("Stats stopped!")