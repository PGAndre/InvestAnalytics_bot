import logging
from datetime import datetime, timedelta

from aiogram.types import CallbackQuery, ChatMemberUpdated
from sqlalchemy import BigInteger

from tgbot.config import Config
from tgbot.models.analytic import Analytic
from tgbot.models.users import User
from tgbot.services.database import create_db_session


async def check(obj):
    config: Config = obj.bot.get('config')
    db_session = await create_db_session(config)
    analytics = await Analytic.get_analytics(db_session=db_session, active=True)
    listof_analytics = []
    for analytic in analytics:
        listof_analytics.append(analytic.telegram_id)
    print(listof_analytics)
    # return obj.from_user.id in config.tg_bot.analytic_ids
    return obj.new_chat_member.user.id in listof_analytics


async def user_add_or_update(obj, role: str, module: str) -> User:
    if type(obj) == CallbackQuery:
        if obj.message.chat.id != obj.from_user.id:
            return
    else:
        if obj.chat.id != obj.from_user.id:
            return
    config = obj.bot.get('config')
    db_session = obj.bot.get('db')
    user_id = obj.from_user.id
    firstname = obj.from_user.first_name
    username = obj.from_user.username
    lastname = obj.from_user.last_name

    role = role
    user: User = await User.get_user(db_session=db_session,
                                     telegram_id=user_id)


    # запущен ли бот в бесплатном режиме.
    # free = config.test.free
    # if free:
    #     subscription_until_str = config.test.free_subtime
    # else:
    #     subscription_until_str = config.test.prod_subtime
    #
    # subscription_until = datetime.strptime(subscription_until_str, '%d/%m/%y %H:%M:%S')


    logger = logging.getLogger(module)
    if not user:
        subscription_until = datetime.utcnow() + timedelta(days=7)
        new_user: User = await User.add_user(db_session=db_session,
                                             subscription_until=subscription_until,
                                             telegram_id=user_id,
                                             first_name=firstname,
                                             last_name=lastname,
                                             username=username,
                                             role=role,
                                             is_botuser=True,
                                             is_member=False
                                             )
        user: User = await User.get_user(db_session=db_session, telegram_id=user_id)
        logger.info(f'новый {role} {user.telegram_id}, {user.username}, {user.first_name} зарегестриован в базе')
        logger.info(f'{user.__dict__}')


    else:
        if user.is_botuser != True:
            updated_user: User = await user.update_user(db_session=db_session,
                                                        is_botuser=True)
            user: User = await User.get_user(db_session=db_session, telegram_id=user_id)
            logger.info(
                f'пользователь подключил бота {user.telegram_id}, {user.username}, {user.first_name}\n')
            logger.info(f'{user.__dict__}')

        if user.role == role:
            return user

        admins = config.tg_bot.admin_ids
        isadmin = user_id in admins
        if user.role == 'tester' and not isadmin:
            return user
        if user.role == 'admin' and isadmin:
            return user
        # если такой пользователь уже найден - меняем ему статус is_member = true
        updated_user: User = await user.update_user(db_session=db_session,
                                                    role=role,
                                                    is_botuser=True)
        user: User = await User.get_user(db_session=db_session, telegram_id=user_id)
        logger.info(
            f'роль пользователя {user.telegram_id}, {user.username}, {user.first_name} обновлена в базе на {role}')
        logger.info(f'{user.__dict__}')



    return user

#проверка кол-ва знаков после запятой
async def num_after_point(x):
    s = str(x)
    if not '.' in s:
        return 0
    return len(s) - s.index('.') - 1


async def chat_member_update(chat_member: ChatMemberUpdated, chat_column_name: str, chat_id: BigInteger, module: str):
    logger=logging.getLogger(module)
    chat_member = chat_member
    config = chat_member.bot.get('config')
    group_id = chat_id

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
    isAnalytic = await check(chat_member)
    if isAnalytic:
        role = 'analytic'
    isadmin = user_id in admins
    if isadmin:
        role = 'admin'


        # запущен ли бот в бесплатном режиме.
    # free = config.test.free
    # if free:
    #     subscription_until_str = config.test.free_subtime
    # else:
    #     subscription_until_str = config.test.prod_subtime
    #
    #
    # subscription_until = datetime.strptime(subscription_until_str, '%d/%m/%y %H:%M:%S')


    incoming_param = chat_column_name
    update_param_false = {incoming_param: False}
    update_param_true = {incoming_param: True}
    add_users_params = {'is_member':False, incoming_param:True}

    if status == 'member' or status == 'creator':
        user: User = await User.get_user(db_session=db_session,
                                         telegram_id=user_id)
        if not user:
            subscription_until = datetime.utcnow() + timedelta(days=7)
            new_user: User = await User.add_user(db_session=db_session,
                                                 subscription_until=subscription_until,
                                                 telegram_id=user_id,
                                                 first_name=firstname,
                                                 last_name=lastname,
                                                 username=username,
                                                 role=role,
                                                 **add_users_params
                                                 )
            user: User = await User.get_user(db_session=db_session, telegram_id=user_id)
            if chat_member.invite_link.is_primary == True:
                logger.info(f'НОВЫЙ пользователь {user.role} {user_id} вошел в группу {chat.title} НЕ ЧЕРЕЗ БОТА по основной ссылке {chat_member.invite_link.invite_link}')
            else:
                logger.info(
                    f'НОВЫЙ пользователь {user.role} {user_id} вошел в группу {chat.title} НЕ ЧЕРЕЗ БОТА по временной ссылке {chat_member.invite_link.invite_link}')
            logger.info(user.__dict__)


        else: #если такой пользователь уже найден - меняем ему статус is_private_group_member=True
            user: User = await User.get_user(db_session=db_session, telegram_id=user_id)
            if user.role == 'tester':
                role = 'tester'
            updated_user: User = await user.update_user(db_session=db_session,
                                                        role=role,
                                                        **update_param_true)
            user: User = await User.get_user(db_session=db_session, telegram_id=user_id)
            if chat_member.invite_link.is_primary == True:
                logger.info(f'пользователь {user.role} {user_id} вошел в группу {chat.title} по основной ссылке {chat_member.invite_link.invite_link}')
            else:
                logger.info(f'пользователь {user.role} {user_id} вошел в группу {chat.title} по временной ссылке {chat_member.invite_link.invite_link}')
            logger.info(user.__dict__)

        if (user.subscription_until <= datetime.utcnow()) and (user.role == 'user'):

            kicked = await chat.kick(user_id, until_date=timedelta(seconds=31))

        invite_link = chat_member.invite_link
        if invite_link.is_primary == False:
            await chat_member.bot.revoke_chat_invite_link(group_id, invite_link=invite_link.invite_link)
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
                                                        role=role,
                                                        **update_param_false)
            user: User = await User.get_user(db_session=db_session, telegram_id=user_id)
            logger.info(f'пользователь {user.role} {user_id} ПОКИНУЛ группу {chat.title}')
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
                                                        role=role,
                                                        **update_param_false)
            user: User = await User.get_user(db_session=db_session, telegram_id=user_id)
            logger.info(f'пользователь {user.role} {user_id} БЫЛ ИСКЛЮЧЕН из группы {chat.title}')
            logger.info(user.__dict__)