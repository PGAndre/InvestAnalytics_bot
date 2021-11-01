import logging
import pprint
from datetime import datetime, timedelta

from aiogram import Dispatcher
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, callback_query
from aiogram.types import ChatMemberUpdated
from aiogram.utils.callback_data import CallbackData

from tgbot.handlers import user
from tgbot.keyboards.callback_datas import user_callback
from tgbot.keyboards.user_menu import *
from tgbot.misc import misc
from tgbot.misc.misc import user_add_or_update
from tgbot.models.users import User


############################ Keyboards #########################################



async def menu(message: Message):
    user: User = await user_add_or_update(message, role='user', module=__name__)
    await message.answer(text=main_menu_message(),
                         reply_markup=main_menu_keyboard())


async def main_menu(query: CallbackQuery):
    user: User = await user_add_or_update(query, role='user', module=__name__)
    await query.answer()
    await query.message.edit_text(
        text=main_menu_message(),
        reply_markup=main_menu_keyboard())


async def first_menu(query: CallbackQuery):
    user: User = await user_add_or_update(query, role='user', module=__name__)
    await query.answer()
    await query.message.edit_text(
        text=first_menu_message(),
        reply_markup=first_menu_keyboard())


async def second_menu(query: CallbackQuery):
    user: User = await user_add_or_update(query, role='user', module=__name__)
    await query.answer()
    await query.message.edit_text(
        text=second_menu_message(),
        reply_markup=second_menu_keyboard())






# async def user_menu(message: Message):
#     inline_btn_1 = InlineKeyboardButton('Первая кнопка!', callback_data='button1')
#     inline_kb1 = InlineKeyboardMarkup().add(inline_btn_1)
#     await message.answer("Первая инлайн кнопка", reply_markup=inline_kb1)
async def myinfo(query: CallbackQuery):
    user: User = await user_add_or_update(query, role='user', module=__name__)
    user_id=query.from_user.id
    username=query.from_user.username
    await query.answer()
    await query.message.answer(text=f'user_id: {user_id}\nusername: {username}')


async def subscription_info(query: CallbackQuery):
    user: User = await user_add_or_update(query, role='user', module=__name__)
    logger = logging.getLogger(__name__)
    user_id=query.from_user.id
    db_session = query.bot.get('db')
    await query.answer()
    subscription_until=user.subscription_until
    logger.info(f'подписка истекает {subscription_until}')
    if user.subscription_until < datetime.utcnow():
        await query.message.answer(text=f'Ваша подписка истекла {subscription_until.date():%d-%m-%Y}')
    else:
        await query.message.answer(text=f'Ваша подписка истекает {subscription_until.date():%d-%m-%Y}')

async def get_invitelink(query: CallbackQuery):
    user: User = await user_add_or_update(query, role='user', module=__name__)
    # если пишут в другой чат, а не боту.
    if query.message.chat.id != query.from_user.id:
        return
    await query.answer()
    config = query.bot.get('config')
    db_session = query.bot.get('db')
    user_id = query.from_user.id
    firstname = query.from_user.first_name
    username = query.from_user.username
    lastname = query.from_user.last_name

    # запущен ли бот в бесплатном режиме.
    logger = logging.getLogger(__name__)


    if user.subscription_until < datetime.utcnow():
        await query.message.edit_text(
            f"Hello, {username} ! \n Ваша подписка истекла. Обновите подписку для получения ссылки на канал.",
    reply_markup=first_menu_keyboard())
    elif user.is_member == True:
        await query.message.answer(
            f"Hello, {username} ! \n Вы уже являетесь подписчиком канала.")
    else:
        invite_link = await query.bot.create_chat_invite_link(chat_id=config.tg_bot.channel_id,
                                                                expire_date=timedelta(hours=1))
        await query.message.answer(f"Hello, {username} ! \n Ваша ссылка для входа в канал: {invite_link.invite_link}")

async def user_help(message: Message):
    user: User = await user_add_or_update(message, role='user', module=__name__)
    if message.chat.id != message.from_user.id:
        return
    await message.answer(
            f'''Общая информация !
   ''')

async def user_start(message: Message):
    user: User = await user_add_or_update(message, role='user', module=__name__)
    await message.answer(
            f'''Hello, {user.username} !
/menu - чтобы попасть в основное меню
/help - Информация.
''')


async def my_chat_member_update(my_chat_member: ChatMemberUpdated):
    my_chat_member = my_chat_member
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
    isadmin = str(user_id) in admins
    if isadmin:
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
    if status == 'member':
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
            logger.info(
                f'новый пользователь подключен к боту {user.telegram_id}, {user.username}, {user.first_name} и зарегестриован в базе')
            logger.info(f'{user.__dict__}')


        else:  # если такой пользователь уже найден - меняем ему статус is_member = true
            updated_user: User = await user.update_user(db_session=db_session,
                                                        role=role,
                                                        is_botuser=True)
            user: User = await User.get_user(db_session=db_session, telegram_id=user_id)
            logger.info(
                f'пользователь переподключеил бота {user.telegram_id}, {user.username}, {user.first_name}\n роль пользователя в базе на {role}')
            logger.info(f'{user.__dict__}')

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
    dp.register_callback_query_handler(first_menu, user_callback.filter(action='sub'))
    dp.register_callback_query_handler(subscription_info, user_callback.filter(action='sub_1'))
    dp.register_callback_query_handler(get_invitelink, user_callback.filter(action='link'))
    dp.register_callback_query_handler(main_menu, user_callback.filter(action='main'))
    dp.register_callback_query_handler(myinfo, user_callback.filter(action='myinfo'))
    dp.register_message_handler(menu, commands=["menu"], state="*")

    # updater.dispatcher.add_handler(CallbackQueryHandler(main_menu, pattern='main'))
    # updater.dispatcher.add_handler(CallbackQueryHandler(first_menu, pattern='m1'))
    # updater.dispatcher.add_handler(CallbackQueryHandler(second_menu, pattern='m2'))
    # updater.dispatcher.add_handler(CallbackQueryHandler(first_submenu,
    #                                                     pattern='m1_1'))
    # updater.dispatcher.add_handler(CallbackQueryHandler(second_submenu,
    #                                                     pattern='m2_1'))

    dp.register_my_chat_member_handler(my_chat_member_update)
    dp.register_message_handler(user_start, commands=["start"], state="*")
    dp.register_message_handler(user_help, commands=["help"], state="*")
