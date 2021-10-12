import pprint
from datetime import datetime, timedelta

from aiogram import Dispatcher
from aiogram.types import Message
from aiogram.types import ChatMemberUpdated

from tgbot.misc import misc
from tgbot.models.users import User


async def user_start(message: Message):
    user = message.from_user.username
    await message.answer(f"Hello, {user} ! \n /predict, чтобы создать прогноз")


async def my_chat_member_update(my_chat_member: ChatMemberUpdated):
    my_chat_member = my_chat_member
    print(f'{my_chat_member} новый мембер')
    config = my_chat_member.bot.get('config')
    db_session = my_chat_member.bot.get('db')
    chat = my_chat_member.chat  # если чат совпадает с чатом из конфига
    user_id = my_chat_member.from_user.id
    firstname = my_chat_member.from_user.first_name
    username = my_chat_member.from_user.username
    lastname = my_chat_member.from_user.last_name

    status = my_chat_member.new_chat_member.values['status']
    role = 'user'
    admins = config.tg_bot.admin_ids
    isAnalytic = await misc.check(my_chat_member)
    if isAnalytic:
        role = 'analytic'
    print(f'Аналитик??? {isAnalytic}')
    isadmin = str(user_id) in admins
    if isadmin:
        role = 'admin'

    if status == 'member':
        print(f'пользователь {user_id} подключил бота')
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
                                                 role=role,
                                                 is_botuser=True,
                                                 is_member=False
                                                 )
            user: User = await User.get_user(db_session=db_session, telegram_id=user_id)
            print(user)
            print(type(user))


        else:  # если такой пользователь уже найден - меняем ему статус is_member = true
            updated_user: User = await user.update_user(db_session=db_session,
                                                        role=role,
                                                        is_botuser=True)
            user: User = await User.get_user(db_session=db_session, telegram_id=user_id)
            print(user)
            print(type(user))
            pprint.pprint(user)

        print(f'ВРЕМЯ СЕЙЧАС {datetime.utcnow()}')


    # elif status == 'left':
    #     print(f'пользователь {user_id} покинул в канал')
    #     user: User = await User.get_user(db_session=db_session,
    #                                      telegram_id=user_id)
    #     if not user:
    #         pass
    #     else:
    #         updated_user: User = await user.update_user(db_session=db_session,
    #                                                     is_member=False,
    #                                                     role=role)
    #         updated_user: User = await User.get_user(db_session=db_session, telegram_id=user_id)
    #         print(updated_user)
    #         print(type(updated_user))
    #         pprint.pprint(updated_user)
    elif status == 'kicked':
        user_id = my_chat_member.chat.id
        print(f'пользователь {user_id} был kicked')
        user: User = await User.get_user(db_session=db_session,
                                         telegram_id=user_id)
        if not user:
            pass
        else:
            updated_user: User = await user.update_user(db_session=db_session,
                                                        role=role,
                                                        is_botuser=False)
            updated_user: User = await User.get_user(db_session=db_session, telegram_id=user_id)
            print(updated_user)
            print(type(updated_user))
            pprint.pprint(updated_user)

    print(status)

    # await User.add_user(db_session=db_session,
    #               subscription_until=datetime.utcnow() + timedelta(days=1000),
    #               is
    #               )


def register_botuser(dp: Dispatcher):
    dp.register_message_handler(user_start, commands=["start"], state="*", is_analytic=True)
    dp.register_my_chat_member_handler(my_chat_member_update)
