import logging
from datetime import datetime

from aiogram.types import CallbackQuery

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
    return obj.from_user.id in listof_analytics


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
    free = config.test.free
    if free:
        subscription_until_str = config.test.free_subtime
    else:
        subscription_until_str = config.test.prod_subtime

    subscription_until = datetime.strptime(subscription_until_str, '%d/%m/%y %H:%M:%S')
    logger = logging.getLogger(module)
    if not user:
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
