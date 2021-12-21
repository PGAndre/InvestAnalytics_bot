import logging
import math
import pprint
from datetime import datetime, timedelta

from aiogram import Dispatcher
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, callback_query, \
    PreCheckoutQuery, SuccessfulPayment, ContentType
from aiogram.types import ChatMemberUpdated
from aiogram.utils.callback_data import CallbackData

from tgbot.config import load_config, Config
from tgbot.filters.botfilters import from_user_chat
from tgbot.handlers import user
from tgbot.keyboards.callback_datas import user_callback, user_predict_callback, user_list_analytic_callback
from tgbot.keyboards.user_menu import *
from tgbot.misc import misc, tinkoff
from tgbot.misc.misc import user_add_or_update
from tgbot.misc.subscriptions import *
from tgbot.models.analytic import Prediction, Analytic
from tgbot.models.users import User


############################ Keyboards #########################################



async def menu(message: Message):
    user: User = await user_add_or_update(message, role='user', module=__name__)
    config = message.bot.get('config')
    free = config.test.free
    if not free or user.role=='tester':
        await message.answer(
            text=main_menu_message(),
            reply_markup=main_menu_keyboard())
    else:
        await message.answer(
            text=main_menu_message(),
            reply_markup=main_menu_keyboard_test())



async def main_menu(query: CallbackQuery):
    user: User = await user_add_or_update(query, role='user', module=__name__)
    await query.answer()
    config = query.bot.get('config')
    free = config.test.free

    if not free or user.role=='tester':
        await query.message.edit_text(
            text=main_menu_message(),
            reply_markup=main_menu_keyboard())
    else:
        await query.message.edit_text(
            text=main_menu_message(),
            reply_markup=main_menu_keyboard_test())



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

async def list_analytics(query: CallbackQuery):
    user: User = await user_add_or_update(query, role='user', module=__name__)
    await query.answer()
    config = query.bot.get('config')
    db_session = query.bot.get('db')
    active_analytics: list[Analytic] = await Analytic.get_analytics(db_session=db_session, active=True)
    markup= InlineKeyboardMarkup(row_width=4)
    for analytic in active_analytics:
        button_text = f'{analytic.Nickname}:{analytic.rating}'
        callback_data = user_list_analytic_callback.new(id=analytic.telegram_id, is_active=True, action='list')
        markup.insert(
            InlineKeyboardButton(text=button_text, callback_data=callback_data)
        )
    markup.row(
        InlineKeyboardButton('Main menu', callback_data=user_callback.new(action='main'))
    )
    await query.message.edit_text(text='Список аналитиков:', reply_markup=markup)

async def choose_analytic(query: CallbackQuery, callback_data: dict):
    db_session = query.bot.get('db')
    logger=logging.getLogger(__name__)
    await query.answer()
    analytic_id=int(callback_data.get('id'))
    analytic: Analytic = await Analytic.get_analytic_by_id(db_session=db_session, telegram_id=analytic_id)
    text = f'''
            Имя: <b>{analytic.Nickname}</b>
Рейтинг: <b>{analytic.rating}</b>
Всего прогнозов: <b>{analytic.predicts_total}</b>
Информация об Аналитике: {analytic.description}
'''
    await query.message.answer(text=text)

async def get_predict_list(query: CallbackQuery):
    user: User = await user_add_or_update(query, role='user', module=__name__)
    if user.subscription_until < datetime.utcnow():
        await query.message.edit_text(
            f"Hello, {user.username} ! \n Ваша подписка истекла. Обновите подписку для получения ссылки на канал.", reply_markup=first_menu_keyboard())
        return
    await query.answer()
    config = query.bot.get('config')
    db_session = query.bot.get('db')
    logger=logging.getLogger(__name__)
    # список всех предиктов is_active
    predictions: list[Prediction] = await Prediction.get_active_predicts(db_session=db_session)
    markup= InlineKeyboardMarkup(row_width=5)
    for prediction in predictions:
        button_text = f'${prediction.ticker}'
        callback_data = user_predict_callback.new(ticker=prediction.ticker)
        markup.insert(
            InlineKeyboardButton(text=button_text, callback_data=callback_data)
        )
    markup.row(
        InlineKeyboardButton('Main menu', callback_data=user_callback.new(action='main'))
    )
    await query.message.edit_text(text='Список активных прогнозов:', reply_markup=markup)


async def predict_info(query: CallbackQuery, callback_data: dict):
    user: User = await user_add_or_update(query, role='user', module=__name__)
    if user.subscription_until < datetime.utcnow():
        await query.message.edit_text(
            f"Hello, {user.username} ! \n Ваша подписка истекла. Обновите подписку для получения ссылки на канал.", reply_markup=first_menu_keyboard())
        return
    config = query.bot.get('config')
    db_session = query.bot.get('db')
    logger=logging.getLogger(__name__)
    await query.answer()
    # logger.info(f"{callback_data}")
    ticker=callback_data.get('ticker')
    # logger.info(f'{ticker}')
    predict = await Prediction.get_predict(db_session=db_session, ticker=ticker)
    name = predict.name
    start_value = predict.start_value
    currency = predict.currency
    start_date = predict.start_date
    predicted_date = predict.predicted_date
    analytic_nickname = predict.analytic.Nickname
    analytic_rating = predict.analytic.rating
    target = predict.predicted_value
    analytic_predicts_total=predict.analytic.predicts_total
    instrument = await tinkoff.search_by_ticker(ticker, config)
    latestcost = await tinkoff.get_latest_cost_history(figi=instrument['figi'], config=config,
                                                       to_time=datetime.utcnow())
    comment = predict.comment
    profit=target-start_value
    sign_profit = math.copysign(1, profit)
    if sign_profit==-1:
        circle='🔴'
    else:
        circle='🟢'
    text = f'''
                🏦<b>${ticker}</b> ({name})
⏱Дата начала: <b>{start_date.date():%d-%m-%Y}</b>                 
⏱Дата окончания:  <b>{predicted_date.date():%d-%m-%Y}</b>
{circle}Прогноз: <b>{start_value} {currency}</b>➡<b>{target} {currency}</b>
Цена сейчас: <b>{latestcost} {currency}</b>
Аналитик: <b>{analytic_nickname}</b>
Рейтинг: <b>{analytic_rating}</b>
Всего прогнозов: <b>{analytic_predicts_total}</b>
Коментарий от аналитика: {comment}'''

    await query.message.answer(text=text,
                                   reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                       [
                                           InlineKeyboardButton(text="Open in Tinkoff",
                                                                url=f'https://www.tinkoff.ru/invest/stocks/{ticker}')
                                       ],
                                   ]))

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


async def subscription_edit(query: CallbackQuery):
    await query.bot.send_invoice(query.from_user.id,
                                 **Ykassa_1month.generate_invoice(),
                                 payload="1monthYkassa")
    await query.bot.send_invoice(query.from_user.id,
                                 **Ykassa_2month.generate_invoice(),
                                 payload="2monthYkassa")
    await query.bot.send_invoice(query.from_user.id,
                                 **Ykassa_3month.generate_invoice(),
                                 payload="3monthYkassa")
    #await query.answer()

async def process_pre_checkout_query(query: PreCheckoutQuery):
    await query.bot.send_message(chat_id=query.from_user.id, text="Спасибо за подписку!")
    await query.bot.answer_pre_checkout_query(pre_checkout_query_id=query.id, ok=True)
    #print(answer)

async def process_success_payment(query: SuccessfulPayment):
    print(query)
    print(query.__dict__)

async def successful_payment(message: Message):
    print(message)
    print(message.__dict__)


async def get_invitelink(query: CallbackQuery):
    user: User = await user_add_or_update(query, role='user', module=__name__)
    # если пишут в другой чат, а не боту.

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
            user: User = await User.get_user(db_session=db_session, telegram_id=user_id)
            if user.role == 'tester':
                role = 'tester'
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
            user: User = await User.get_user(db_session=db_session, telegram_id=user_id)
            if user.role == 'tester':
                role = 'tester'
            updated_user: User = await user.update_user(db_session=db_session,
                                                        role=role,
                                                        is_botuser=False)
            updated_user: User = await User.get_user(db_session=db_session, telegram_id=user_id)
            print(updated_user)
            print(type(updated_user))
            pprint.pprint(updated_user)

    print(status)

    # await User.add_user(db_session=db_session,
    #               subscrip81764678:TEST:30755 tion_until=datetime.utcnow() + timedelta(days=1000),
    #               is
    #               )


def register_botuser(dp: Dispatcher):
    dp.register_pre_checkout_query_handler(process_pre_checkout_query, state="*")
    dp.register_callback_query_handler(first_menu, user_callback.filter(action='sub'), chat_type="private")
    dp.register_callback_query_handler(subscription_info, user_callback.filter(action='sub_1'), chat_type="private")
    dp.register_callback_query_handler(subscription_edit, user_callback.filter(action='sub_2'), chat_type="private")
    dp.register_callback_query_handler(get_predict_list, user_callback.filter(action='pred'), state="*", chat_type="private")
    dp.register_callback_query_handler(predict_info, user_predict_callback.filter(), state="*", chat_type="private")
    dp.register_callback_query_handler(list_analytics, user_callback.filter(action='analytic'), state="*", chat_type="private")
    dp.register_callback_query_handler(choose_analytic, user_list_analytic_callback.filter(), state="*", chat_type="private")
    dp.register_callback_query_handler(get_invitelink, user_callback.filter(action='link'), chat_type="private")
    dp.register_callback_query_handler(main_menu, user_callback.filter(action='main'), chat_type="private")
    dp.register_callback_query_handler(myinfo, user_callback.filter(action='myinfo'), chat_type="private")
    dp.register_message_handler(menu, commands=["menu"], state="*", chat_type="private")

    # updater.dispatcher.add_handler(CallbackQueryHandler(main_menu, pattern='main'))
    # updater.dispatcher.add_handler(CallbackQueryHandler(first_menu, pattern='m1'))
    # updater.dispatcher.add_handler(CallbackQueryHandler(second_menu, pattern='m2'))
    # updater.dispatcher.add_handler(CallbackQueryHandler(first_submenu,
    #                                                     pattern='m1_1'))
    # updater.dispatcher.add_handler(CallbackQueryHandler(second_submenu,
    #                                                     pattern='m2_1'))

    dp.register_my_chat_member_handler(my_chat_member_update)
    dp.register_message_handler(user_start, commands=["start"], state="*", chat_type="private")
    dp.register_message_handler(user_help, commands=["help"], state="*", chat_type="private")
    dp.register_message_handler(successful_payment, content_types = ContentType.SUCCESSFUL_PAYMENT)
