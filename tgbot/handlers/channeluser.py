import logging
import pprint
from datetime import datetime, timedelta

from aiogram import Dispatcher
from aiogram.types import Message
from aiogram.types import ChatMemberUpdated

from tgbot.misc import misc
from tgbot.models.users import User


async def chat_member_update(chat_member: ChatMemberUpdated):
    logger=logging.getLogger(__name__)
    chat_member = chat_member
    #print(f'{chat_member} новый мембер')
    config = chat_member.bot.get('config')

    db_session = chat_member.bot.get('db')
    #это надо реализовать фильтром
    if chat_member.chat.id != config.tg_bot.channel_id:
        return
    chat = chat_member.chat# если чат совпадает с чатом из конфига
    user_id = chat_member.from_user.id
    firstname = chat_member.from_user.first_name
    username = chat_member.from_user.username
    lastname = chat_member.from_user.last_name

    status = chat_member.new_chat_member.values['status']
    role = 'user'
    admins = config.tg_bot.admin_ids
    isAnalytic = await misc.check(chat_member)
    if isAnalytic:
        role = 'analytic'
    isadmin = user_id in admins
    if isadmin:
        role = 'admin'

        # запущен ли бот в бесплатном режиме.
    free = config.test.free
    if free:
        subscription_until_str = config.test.free_subtime
    else:
        subscription_until_str = config.test.prod_subtime


    subscription_until = datetime.strptime(subscription_until_str, '%d/%m/%y %H:%M:%S')

    # print("The type of the date is now", type(subscription_until))
    # print("The date is", subscription_until)

    if status == 'member' or status == 'creator':
        user: User = await User.get_user(db_session=db_session,
                                         telegram_id=user_id)
        if not user:
            new_user: User = await User.add_user(db_session=db_session,
                                                 subscription_until=subscription_until,
                                                 telegram_id=user_id,
                                                 first_name=firstname,
                                                 last_name=lastname,
                                                 username=username,
                                                 role=role
                                                 )
            user: User = await User.get_user(db_session=db_session, telegram_id=user_id)
            if chat_member.invite_link.is_primary == True:
                logger.info(f'НОВЫЙ пользователь {user.role} {user_id} вошел в канал НЕ ЧЕРЕЗ БОТА по основной ссылке {chat_member.invite_link.invite_link}')
            else:
                logger.info(
                    f'НОВЫЙ пользователь {user.role} {user_id} вошел в канал НЕ ЧЕРЕЗ БОТА по временной ссылке {chat_member.invite_link.invite_link}')
            logger.info(user.__dict__)


        else: #если такой пользователь уже найден - меняем ему статус is_member = true
            updated_user: User = await user.update_user(db_session=db_session,
                                                        is_member=True,
                                                        role=role)
            user: User = await User.get_user(db_session=db_session, telegram_id=user_id)
            if chat_member.invite_link.is_primary == True:
                logger.info(f'пользователь {user.role} {user_id} вошел в канал по основной ссылке {chat_member.invite_link.invite_link}')
            else:
                logger.info(f'пользователь {user.role} {user_id} вошел в канал по временной ссылке {chat_member.invite_link.invite_link}')
            logger.info(user.__dict__)

        if (user.subscription_until <= datetime.utcnow()) and (user.role == 'user'):

            kicked = await chat.kick(user_id, until_date=timedelta(seconds=31))

        invite_link = chat_member.invite_link
        if invite_link.is_primary == False:
            await chat_member.bot.revoke_chat_invite_link(config.tg_bot.channel_id, invite_link=invite_link.invite_link)
            logger.info(f'временная ссылка {chat_member.invite_link.invite_link} была отозвана и больше не активна')


    elif status == 'left':
        #print(f'пользователь {user_id} покинул в канал')
        user: User = await User.get_user(db_session=db_session,
                                         telegram_id=user_id)
        if not user:
            pass
        else:
            updated_user: User = await user.update_user(db_session=db_session,
                                                        is_member=False,
                                                        role=role)
            user: User = await User.get_user(db_session=db_session, telegram_id=user_id)
            logger.info(f'пользователь {user.role} {user_id} ПОКИНУЛ канал')
            logger.info(user.__dict__)
    elif status == 'kicked':
        user_id = chat_member.new_chat_member.user.id
        user: User = await User.get_user(db_session=db_session,
                                         telegram_id=user_id)
        if not user:
            pass
        else:
            updated_user: User = await user.update_user(db_session=db_session,
                                                        is_member=False,
                                                        role=role)
            user: User = await User.get_user(db_session=db_session, telegram_id=user_id)
            logger.info(f'пользователь {user.role} {user_id} БЫЛ ИСКЛЮЧЕН из канала')
            logger.info(user.__dict__)



def register_channeluser(dp: Dispatcher):
    dp.register_chat_member_handler(chat_member_update)
