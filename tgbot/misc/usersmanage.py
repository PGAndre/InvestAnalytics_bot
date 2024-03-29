import asyncio
import logging
from datetime import datetime, timedelta

from aiogram import Bot
from aiogram.utils.exceptions import BotBlocked
from sqlalchemy.orm import sessionmaker

from tgbot.config import load_config, Config
from tgbot.keyboards.user_menu import first_menu_keyboard
from tgbot.models.admin import Message
from tgbot.models.users import User
from tgbot.services.database import create_db_session


async def kick_private_group_users():
    config: Config = load_config()
    db_session = await create_db_session(config)
    users = await User.get_private_group_users_sub(db_session=db_session, time=datetime.now(), is_private_group_member=True)
    bot = Bot(token=config.tg_bot.token, parse_mode='HTML')
    channel_id = config.tg_bot.channel_id
    private_group_id = config.tg_bot.private_group_id
    botobj = await bot.get_me()
    botname = botobj.username
    logger = logging.getLogger(__name__)

    for user in users:
        await asyncio.sleep(0.05)
        user_id = user.telegram_id
        try:
            await bot.unban_chat_member(chat_id=private_group_id, user_id=user_id)
            # await bot.kick_chat_member(chat_id=channel_id, user_id=user_id, until_date=timedelta(seconds=60))
            # logger.info(f'пользователь {user.__dict__} был исключен из канала в связи с тем, что не был занесен в базу')
        except:
            logger.info(
                f'нельзя кикнуть пользователя {user.__dict__}{botobj}')
        # await bot.unban_chat_member(chat_id=channel_id, user_id=user_id)
        # await bot.kick_chat_member(chat_id=channel_id, user_id=user_id, until_date=timedelta(seconds=60))
        logger.info(f'пользователь {user.__dict__} был исключен из приватной группы в связи с истекшей подпиской')

# запускать каждый день!
async def kick_users():
    config: Config = load_config()
    db_session = await create_db_session(config)
    users = await User.get_users_sub(db_session=db_session, time=datetime.now(), is_member=True)
    bot = Bot(token=config.tg_bot.token, parse_mode='HTML')
    channel_id = config.tg_bot.channel_id
    private_group_id = config.tg_bot.private_group_id
    botobj = await bot.get_me()
    botname = botobj.username
    logger = logging.getLogger(__name__)

    for user in users:
        await asyncio.sleep(0.05)
        user_id = user.telegram_id
        try:
            await bot.unban_chat_member(chat_id=channel_id, user_id=user_id)
            # await bot.kick_chat_member(chat_id=channel_id, user_id=user_id, until_date=timedelta(seconds=60))
            # logger.info(f'пользователь {user.__dict__} был исключен из канала в связи с тем, что не был занесен в базу')
        except:
            logger.info(
                f'нельзя кикнуть пользователя {user.__dict__}{botobj}')
        # await bot.unban_chat_member(chat_id=channel_id, user_id=user_id)
        # await bot.kick_chat_member(chat_id=channel_id, user_id=user_id, until_date=timedelta(seconds=60))
        logger.info(f'пользователь {user.__dict__} был исключен из канала в связи с истекшей подпиской')

        if user.is_botuser:
            try:
                await bot.send_message(chat_id=user_id,
                                       text=f'ваша подписка истекла. \nпройдите по ссылке для продления:', reply_markup=first_menu_keyboard())
                logger.info(f'уведомление об исключчении из канала {channel_id} для {user.__dict__}')
            except:
                logger.exception(
                    f'нельзя отправить сообщение пользователю {user.__dict__}, т.к он отключил бота {botobj}')


# запускать каждый день!
async def kick_users_notmember():
    config: Config = load_config()
    db_session = await create_db_session(config)
    users = await User.get_users_member(db_session=db_session, is_member=False)
    bot = Bot(token=config.tg_bot.token, parse_mode='HTML')
    channel_id = config.tg_bot.channel_id
    botobj = await bot.get_me()
    botname = botobj.username
    logger = logging.getLogger(__name__)
    for user in users:
        await asyncio.sleep(0.05)
        user_id = user.telegram_id
        try:
            await bot.unban_chat_member(chat_id=channel_id, user_id=user_id)
            # await bot.kick_chat_member(chat_id=channel_id, user_id=user_id, until_date=timedelta(seconds=60))
            # logger.info(f'пользователь {user.__dict__} был исключен из канала в связи с тем, что не был занесен в базу')
        except:
            logger.info(
                f'нельзя кикнуть пользователя, т.к он уже покинул чат  {user.__dict__}{botobj}')

async def notify_users_with_active_sub_notmembers():
    config: Config = load_config()
    # date_time_str = config.test.free_subtime
    # date_time_obj = datetime.strptime(date_time_str, '%d/%m/%y %H:%M:%S')
    #
    # print("The type of the date is now", type(date_time_obj))
    # print("The date is", date_time_obj)
    db_session = await create_db_session(config)
    users = await User.get_users_sub(db_session=db_session, time=datetime.now() + timedelta(days=4), is_member=False)
    # users = [x for x in users if x.is_botuser == True]
    # users = [x for x in users if x.subscription_until > datetime.now()+timedelta(days=1)]
    bot = Bot(token=config.tg_bot.token, parse_mode='HTML')
    channel_id = config.tg_bot.channel_id
    botobj = await bot.get_me()
    botname = botobj.username
    logger = logging.getLogger(__name__)
    for user in users:
        if (user.is_botuser == True) and (user.subscription_until > datetime.now() + timedelta(days=1)):
            user_id = user.telegram_id
            try:
                await bot.send_message(chat_id=user_id,
                                       text=f'ваша подписка истекает {user.subscription_until.date():%d-%m-%Y}\nпройдите по ссылке для продления:', reply_markup=first_menu_keyboard())
                logger.info(f'уведомление об истекающей подписке на канал {channel_id} для {user.__dict__}')
            except:
                await user.update_user(db_session=db_session,
                                       is_botuser=False)
                logger.exception(
                    f'нельзя отправить сообщение пользователю {user.__dict__}, т.к он отключил бота {botobj}')


# запускать каждый день
async def notify_users_with_active_sub():
    config: Config = load_config()
    # date_time_str = config.test.free_subtime
    # date_time_obj = datetime.strptime(date_time_str, '%d/%m/%y %H:%M:%S')
    #
    # print("The type of the date is now", type(date_time_obj))
    # print("The date is", date_time_obj)
    db_session = await create_db_session(config)
    users = await User.get_users_sub(db_session=db_session, time=datetime.now() + timedelta(days=4), is_member=True)
    # users = [x for x in users if x.is_botuser == True]
    # users = [x for x in users if x.subscription_until > datetime.now()+timedelta(days=1)]
    bot = Bot(token=config.tg_bot.token, parse_mode='HTML')
    channel_id = config.tg_bot.channel_id
    botobj = await bot.get_me()
    botname = botobj.username
    logger = logging.getLogger(__name__)
    for user in users:
        if (user.is_botuser == True) and (user.subscription_until > datetime.now() + timedelta(days=1)):
            user_id = user.telegram_id
            try:
                await bot.send_message(chat_id=user_id,
                                       text=f'ваша подписка истекает {user.subscription_until.date():%d-%m-%Y}\nпройдите по ссылке для продления:', reply_markup=first_menu_keyboard())
                logger.info(f'уведомление об истекающей подписке на канал {channel_id} для {user.__dict__}')
            except:
                await user.update_user(db_session=db_session,
                                       is_botuser=False)
                logger.exception(
                    f'нельзя отправить сообщение пользователю {user.__dict__}, т.к он отключил бота {botobj}')


# запуск раз в неделю
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
        if (user.is_botuser == True) and (user.subscription_until > datetime.now() - timedelta(days=7)):
            user_id = user.telegram_id
            try:
                await bot.send_message(chat_id=user_id,
                                       text=f'ваша подписка истекла. \nпройдите по ссылке для продления:', reply_markup=first_menu_keyboard())
                logger.info(f'уведомление об истекшей подписке на канал {channel_id} для {user.__dict__}')
            except:
                await user.update_user(db_session=db_session,
                                       is_botuser=False)
                logger.exception(
                    f'нельзя отправить сообщение пользователю {user.__dict__}, т.к он отключил бота {botobj}')



async def bot_messaging(bot: Bot):
    messages = await Message.get_active_messages(db_session=bot.get("db"))
    for message in messages:
        message_datetime = datetime.combine(message.message_date, message.message_time)
        if datetime.utcnow() >= message.start_date and datetime.utcnow() <= message.end_date:
            if message.type == 'once':
                if datetime.utcnow() >= message_datetime and message.last_sent_date is None:
                    users = await User.get_users_by_query(db_session=bot.get("db"), query=message.recipients_query)
                    await User.send_messages_to_userslist(users=users, message=message, bot=bot, module=__name__)









# async def add_user_tochannel():
#     config: Config = load_config()
#     db_session = await create_db_session(config)
#     bot = Bot(token=config.tg_bot.token, parse_mode='HTML')
#     await bot.


#asyncio.run(kick_users_notmember())
# asyncio.run(notify_users_with_active_sub())
# asyncio.run(notify_users_with_inactive_sub())
# asyncio.run(kick_users())
# asyncio.run(kick_private_group_users())
