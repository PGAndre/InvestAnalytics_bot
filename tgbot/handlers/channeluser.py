import logging
from datetime import datetime, timedelta

from aiogram import Dispatcher
from aiogram.types import Message
from aiogram.types import ChatMemberUpdated

from tgbot.filters.botfilters import *
from tgbot.misc import misc
from tgbot.models.users import User


async def chat_member_update(chat_member: ChatMemberUpdated):
    logger=logging.getLogger(__name__)
    chat_member = chat_member
    config = chat_member.bot.get('config')

    db_session = chat_member.bot.get('db')
    #это надо реализовать фильтром
    chat = chat_member.chat# если чат совпадает с чатом из конфига
    user_id = chat_member.new_chat_member.user.id
    firstname = chat_member.new_chat_member.user.first_name
    username = chat_member.new_chat_member.user.username
    lastname = chat_member.new_chat_member.user.last_name

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
            user: User = await User.get_user(db_session=db_session, telegram_id=user_id)
            if user.role == 'tester':
                role = 'tester'
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
        user: User = await User.get_user(db_session=db_session,
                                         telegram_id=user_id)
        if not user:
            pass
        else:
            user: User = await User.get_user(db_session=db_session, telegram_id=user_id)
            if user.role == 'tester':
                role = 'tester'
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
            user: User = await User.get_user(db_session=db_session, telegram_id=user_id)
            if user.role == 'tester':
                role = 'tester'
            updated_user: User = await user.update_user(db_session=db_session,
                                                        is_member=False,
                                                        role=role)
            user: User = await User.get_user(db_session=db_session, telegram_id=user_id)
            logger.info(f'пользователь {user.role} {user_id} БЫЛ ИСКЛЮЧЕН из канала')
            logger.info(user.__dict__)


async def private_group_update(chat_member: ChatMemberUpdated):
    config = chat_member.bot.get('config')
    chat_id = config.tg_bot.private_group_id
    await misc.chat_member_update(chat_member, chat_column_name = 'is_private_group_member', chat_id=chat_id, module=__name__)

async def group_member_update(chat_member: ChatMemberUpdated):
    logger=logging.getLogger(__name__)
    chat_member = chat_member
    config = chat_member.bot.get('config')
    chat = chat_member.chat# если чат совпадает с чатом из конфига
    user_id = chat_member.from_user.id
    status = chat_member.new_chat_member.values['status']
    role = 'user'
    admins = config.tg_bot.admin_ids
    isAnalytic = await misc.check(chat_member)
    if isAnalytic:
        role = 'analytic'
    isadmin = user_id in admins
    if isadmin:
        role = 'admin'

    if role == 'analytic' or role == 'admin':
        return
    if status == 'member' or status == 'creator':

        kicked = await chat.kick(user_id, until_date=timedelta(seconds=31))

        logger.info(f'пользователь {chat_member.from_user.id} {chat_member.from_user.username} попытался войти в \nприватную группу {chat_member.chat.id} {chat_member.chat.title} привязанную каналу и будет кикнут')


    elif status == 'left':
        pass
    elif status == 'kicked':
       logger.info(f'пользователь {chat_member.from_user.id} {chat_member.from_user.username} был кикнут \nиз группы {chat_member.chat.id} {chat_member.chat.title} привязанную каналу ')




def register_channeluser(dp: Dispatcher):
    dp.register_chat_member_handler(group_member_update, group_chat_member)
    dp.register_chat_member_handler(chat_member_update, channel_chat_member)
    dp.register_chat_member_handler(private_group_update, private_group_member_filter)


