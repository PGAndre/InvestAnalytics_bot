import pprint
from datetime import datetime, timedelta

from aiogram import Dispatcher
from aiogram.types import Message
from aiogram.types import ChatMemberUpdated

from tgbot.misc import misc
from tgbot.models.users import User


async def user_start(message: Message):
    user = message.from_user.username
    await message.reply(f"Hello, {user} ! \n /predict, чтобы создать прогноз")


async def chat_member_update(chat_member: ChatMemberUpdated):
    chat_member = chat_member
    print(f'{chat_member} новый мембер')
    config = chat_member.bot.get('config')
    db_session = chat_member.bot.get('db')
    if chat_member.chat.id == config.tg_bot.channel_id:  # если чат совпадает с чатом из конфига
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
        print(f'Аналитик??? {isAnalytic}')
        isadmin = str(user_id) in admins
        if isadmin:
            role = 'admin'


        if status == 'member':
            print(f'пользователь {user_id} вошел в канал')
            user: User = await User.get_user(db_session=db_session,
                                             telegram_id=user_id)
            print(user)
            if not user:
                new_user: User = await User.add_user(db_session=db_session,
                                                     subscription_until=datetime.utcnow() + timedelta(days=1000),
                                                     telegram_id=user_id,
                                                     first_name=firstname,
                                                     last_name=lastname,
                                                     username=username,
                                                     role=role
                                                     )
                new_user: User = await User.get_user(db_session=db_session, telegram_id=user_id)
                print(new_user)
                print(type(new_user))


            else: #если такой пользователь уже найден - меняем ему статус is_member = true
                updated_user: User = await user.update_user(db_session=db_session,
                                                            is_member=True,
                                                            role=role)
                updated_user: User = await User.get_user(db_session=db_session, telegram_id=user_id)
                print(updated_user)
                print(type(updated_user))
                pprint.pprint(updated_user)

        elif status == 'left':
            print(f'пользователь {user_id} покинул в канал')
            user: User = await User.get_user(db_session=db_session,
                                             telegram_id=user_id)
            if not user:
                pass
            else:
                updated_user: User = await user.update_user(db_session=db_session,
                                                            is_member=False,
                                                            role=role)
                updated_user: User = await User.get_user(db_session=db_session, telegram_id=user_id)
                print(updated_user)
                print(type(updated_user))
                pprint.pprint(updated_user)
        print(status)

        # await User.add_user(db_session=db_session,
        #               subscription_until=datetime.utcnow() + timedelta(days=1000),
        #               is
        #               )


def register_user(dp: Dispatcher):
    dp.register_message_handler(user_start, commands=["start"], state="*")
    dp.register_chat_member_handler(chat_member_update)
