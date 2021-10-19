import asyncio
import logging
from datetime import datetime, timedelta

from aiogram import Bot
from aiogram.utils.exceptions import BotBlocked

from tgbot.config import load_config, Config
from tgbot.models.users import User
from tgbot.services.database import create_db_session

#запускать каждый день!
async def kick_users():

    config: Config = load_config()
    db_session = await create_db_session(config)
    users = await User.get_users_sub(db_session=db_session, time=datetime.now(), is_member=True)
    bot = Bot(token=config.tg_bot.token, parse_mode='HTML')
    channel_id = config.tg_bot.channel_id
    botobj = await bot.get_me()
    botname = botobj.username

    for user in users:
        logger = logging.getLogger(__name__)
        user_id = user.telegram_id
        await bot.kick_chat_member(chat_id=channel_id, user_id=user_id, until_date=timedelta(seconds=31))
        logger.info(f'пользователь {user.__dict__} был исключен из канала в связи с истекшей подпиской')
        if user.is_botuser:
            try:
                await bot.send_message(chat_id=user_id, text=f'ваша подписка истекла. \nпройдите по ссылке для продления: ТУТ БУДЕТ КЛАВИАТУРА')
                logger.info(f'уведомление об исключчении из канала {channel_id} для {user}')
            except BotBlocked:
                logger.exception(f'нельзя отправить сообщение пользователю {user}, т.к он отключил бота {botobj}')

#запускать каждый день
async def notify_users_with_active_sub():
    config: Config = load_config()
    # date_time_str = config.test.free_subtime
    # date_time_obj = datetime.strptime(date_time_str, '%d/%m/%y %H:%M:%S')
    #
    # print("The type of the date is now", type(date_time_obj))
    # print("The date is", date_time_obj)
    db_session = await create_db_session(config)
    users = await User.get_users_sub(db_session=db_session, time=datetime.now()+timedelta(days=4), is_member=True)
    # users = [x for x in users if x.is_botuser == True]
    # users = [x for x in users if x.subscription_until > datetime.now()+timedelta(days=1)]
    bot = Bot(token=config.tg_bot.token, parse_mode='HTML')
    channel_id = config.tg_bot.channel_id
    botobj = await bot.get_me()
    botname = botobj.username
    logger = logging.getLogger(__name__)
    for user in users:
        if (user.is_botuser == True) and (user.subscription_until > datetime.now()+timedelta(days=1)):
            user_id = user.telegram_id
            try:
                await bot.send_message(chat_id=user_id,
                                       text=f'ваша подписка истекает {user.subscription_until.date()}, для продления пройдите по ссылке ниже ююю ТУТ БУДЕТ КНОПКА')
                logger.info(f'уведомление об истекающей подписке на канал {channel_id} для {user}')
            except BotBlocked:
                logger.exception(f'нельзя отправить сообщение пользователю {user}, т.к он отключил бота {botobj}')

#запуск раз в неделю
async def notify_users_with_inactive_sub():
    logger = logging.getLogger(__name__)
    config: Config = load_config()
    db_session = await create_db_session(config)
    users = await User.get_users_sub(db_session=db_session, time=datetime.now() - timedelta(days=6), is_member=False)
    # users = [x for x in users if x.is_botuser == True]
    bot = Bot(token=config.tg_bot.token, parse_mode='HTML')
    channel_id = config.tg_bot.channel_id
    botobj = await bot.get_me()
    botname = botobj.username

    for user in users:
        print(user)
        if (user.is_botuser==True) and (user.subscription_until > datetime.now() -timedelta(days=7)):
            user_id = user.telegram_id
            try:
                await bot.send_message(chat_id=user_id,
                                       text=f'ваша подписка истекла , для продления пройдите по ссылке ниже ююю ТУТ БУДЕТ КНОПКА')
                logger.info(f'уведомление об истекшей подписке на канал {channel_id} для {user}')
            except BotBlocked:
                logger.exception(f'нельзя отправить сообщение пользователю {user}, т.к он отключил бота {botobj}')

# async def add_user_tochannel():
#     config: Config = load_config()
#     db_session = await create_db_session(config)
#     bot = Bot(token=config.tg_bot.token, parse_mode='HTML')
#     await bot.


asyncio.run(notify_users_with_active_sub())
asyncio.run(notify_users_with_inactive_sub())
asyncio.run(kick_users())
