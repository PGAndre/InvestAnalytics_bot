import logging
from datetime import datetime

from aiogram import Dispatcher
from aiogram.types import Message

from tgbot.models.users import User


async def admin_start(message: Message):
    if message.chat.id != query.from_user.id:
        return
    config = message.bot.get('config')
    db_session = message.bot.get('db')
    user_id = message.from_user.id
    firstname = message.from_user.first_name
    username = message.from_user.username
    lastname = message.from_user.last_name

    role = 'admin'
    user: User = await User.get_user(db_session=db_session,
                                     telegram_id=user_id)
    # запущен ли бот в бесплатном режиме.
    free = config.test.free
    if free:
        subscription_until_str = config.test.free_subtime
    else:
        subscription_until_str = config.test.prod_subtime

    subscription_until = datetime.strptime(subscription_until_str, '%d/%m/%y %H:%M:%S')
    logger = logging.getLogger(__name__)
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
        logger.info(f'новый админ {user.telegram_id}, {user.username}, {user.first_name} зарегестриован в базе')
        logger.info(f'{user.__dict__}')


    else:  # если такой пользователь уже найден - меняем ему статус is_member = true
        updated_user: User = await user.update_user(db_session=db_session,
                                                    role=role,
                                                    is_botuser=True)
        user: User = await User.get_user(db_session=db_session, telegram_id=user_id)
        logger.info(f'роль пользователя {user.telegram_id}, {user.username}, {user.first_name} обновлена в базе на Admin')
        logger.info(f'{user.__dict__}')

    start_text='Hello, admin!'
    await message.answer(text=start_text)


def register_admin(dp: Dispatcher):
    dp.register_message_handler(admin_start, commands=["start"], state="*", is_admin=True)
    pass
