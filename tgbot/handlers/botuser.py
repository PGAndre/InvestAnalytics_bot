import logging
import math
import pprint
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta

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
from tgbot.models.admin import Document
from tgbot.models.analytic import Prediction, Analytic
from tgbot.models.orders import Product, PaymentInfo
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

async def link_menu(query: CallbackQuery):
    user: User = await user_add_or_update(query, role='user', module=__name__)
    await query.answer()
    await query.message.edit_text(
        text=link_menu_message(),
        reply_markup=link_menu_keyboard())






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
    if user.subscription_until < datetime.utcnow():
        await query.message.edit_text(
            f"Здравствуйте! \nВаша подписка истекла. Обновите подписку для получения ссылки на канал.", reply_markup=first_menu_keyboard())
        return
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
        InlineKeyboardButton('Главное меню', callback_data=user_callback.new(action='main'))
    )
    await query.message.edit_text(text='Список аналитиков:', reply_markup=markup)

async def choose_analytic(query: CallbackQuery, callback_data: dict):
    user: User = await user_add_or_update(query, role='user', module=__name__)
    if user.subscription_until < datetime.utcnow():
        await query.message.edit_text(
            f"Здравствуйте! \nВаша подписка истекла. Обновите подписку для получения ссылки на канал.", reply_markup=first_menu_keyboard())
        return
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
            f"Здравствуйте! \nВаша подписка истекла. Обновите подписку для получения ссылки на канал.", reply_markup=first_menu_keyboard())
        return
    await query.answer()
    config = query.bot.get('config')
    db_session = query.bot.get('db')
    logger=logging.getLogger(__name__)
    # список всех предиктов is_active
    predictions: list[Prediction] = await Prediction.get_active_predicts(db_session=db_session)
    markup= InlineKeyboardMarkup(row_width=4)
    db_session = query.bot.get('db')
    active_analytics: list[Analytic] = await Analytic.get_analytics(db_session=db_session, active=True)
    for active_analytic in active_analytics:
        analytic_id = active_analytic.telegram_id
        active_predicts: list[Prediction] = await Prediction.get_predict_by_analytic(db_session=db_session,
                                                                                        analytic_id=analytic_id)
    # for prediction in predictions:
    #     pass
        predictions_long = []
        predictions_short = []
        active_preicts_list = []
        for prediction in active_predicts:
            active_preicts_list.append(prediction)
            target = prediction.predicted_value
            start_value = prediction.start_value
            profit = target - start_value
            sign_profit = math.copysign(1, profit)
            if sign_profit == 1:
                predictions_long.append(prediction)
            elif sign_profit == -1:
                predictions_short.append(prediction)
        prediction_long_buttons = []
        for prediction_long in predictions_long:
            circle = '🟢'
            button_text = f'{circle}${prediction_long.ticker}'
            callback_data = user_predict_callback.new(ticker=prediction_long.ticker, action="info")
            button = InlineKeyboardButton(text=button_text, callback_data=callback_data)
            prediction_long_buttons.append(button)
            # markup.insert(
            #     InlineKeyboardButton(text=button_text, callback_data=callback_data)
            # )
        prediction_short_buttons = []
        for prediction_short in predictions_short:
            circle = '🔴'
            button_text = f'{circle}${prediction_short.ticker}'
            callback_data = user_predict_callback.new(ticker=prediction_short.ticker, action="info")
            button = InlineKeyboardButton(text=button_text, callback_data=callback_data)
            prediction_short_buttons.append(button)


            # button_text = f'{circle}${prediction.ticker}'
            # callback_data = user_predict_callback.new(ticker=prediction.ticker)
            # markup.insert(
            #     InlineKeyboardButton(text=button_text, callback_data=callback_data)
            # )
        callback_data = user_list_analytic_callback.new(id=analytic_id, is_active=True, action='list')
        if active_preicts_list != []:
            markup.add(InlineKeyboardButton(text=f'Прогнозы Аналитика 📈{active_analytic.Nickname}', callback_data=callback_data))
        markup.add(*prediction_long_buttons)
        markup.add(*prediction_short_buttons)
    markup.row(
        InlineKeyboardButton('Главное меню', callback_data=user_callback.new(action='main'))
    )
    await query.message.edit_text(text='Список активных прогнозов:', reply_markup=markup)


async def predict_info(query: CallbackQuery, callback_data: dict):
    user: User = await user_add_or_update(query, role='user', module=__name__)
    if user.subscription_until < datetime.utcnow():
        await query.message.edit_text(
            f"Здравствуйте! \nВаша подписка истекла. Обновите подписку для получения ссылки на канал.", reply_markup=first_menu_keyboard())
        return
    config = query.bot.get('config')
    db_session = query.bot.get('db')
    logger=logging.getLogger(__name__)
    await query.answer()
    # logger.info(f"{callback_data}")
    ticker=callback_data.get('ticker')
    # logger.info(f'{ticker}')
    predict = await Prediction.get_predict(db_session=db_session, ticker=ticker)
#     name = predict.name
#     start_value = predict.start_value
#     start_date = predict.start_date
#     predicted_date = predict.predicted_date
#     analytic_nickname = predict.analytic.Nickname
#     analytic_rating = predict.analytic.rating
#     target = predict.predicted_value
#     analytic_predicts_total=predict.analytic.predicts_total
#     # latestcost = await tinkoff.get_latest_cost_history(figi=instrument['figi'], config=config,
#     #                                                    to_time=datetime.utcnow())
#     comment = predict.comment
#     profit=target-start_value
#     sign_profit = math.copysign(1, profit)
#     if sign_profit==-1:
#         circle='🔴'
#     else:
#         circle='🟢'
#     risk = '⚡' * risk_level
#     if risk_level == 0:
#         risk = '⚡⚡'
#     text = f'''
#                 🏦<b>${ticker}</b> ({name})
# ⏱Дата начала: <b>{start_date.date():%d-%m-%Y}</b>
# ⏱Дата окончания:  <b>{predicted_date.date():%d-%m-%Y}</b>
# {circle}Прогноз: <b>{start_value} {currency}</b>➡<b>{target} {currency}</b>
# Цена сейчас: <b>{latestcost} {currency}</b>
# Уровень риска: {risk}
# Аналитик: <b>{analytic_nickname}</b>
# Рейтинг: <b>{analytic_rating}</b>
# Всего прогнозов: <b>{analytic_predicts_total}</b>
# Коментарий от аналитика: {comment}'''
##     risk_level = predict.risk_level
    currency = predict.currency
    instrument = await tinkoff.search_by_ticker(ticker, config)
    latestcost = await tinkoff.latestcost(figi=instrument['figi'], config=config)
    markup= InlineKeyboardMarkup(row_width=4)
    markup.row(InlineKeyboardButton(text="Cсылка на прогноз", url=f'{predict.message_url}'))
    markup.insert(InlineKeyboardButton(text="Open in Tinkoff", url=f'https://www.tinkoff.ru/invest/stocks/{ticker}'))
    markup.row(InlineKeyboardButton(text='К списку активных прогнозов',
                                    callback_data=user_predict_callback.new(ticker=ticker, action='back')))
    markup.row(
        InlineKeyboardButton('Главное меню', callback_data=user_callback.new(action='main'))
    )
    new_text = await predict.edit_message_text(db_session=db_session)
    new_text += f'\nЦена сейчас: <b>{latestcost} {currency}</b>'
    # await query.message.answer(text=new_text,
    #                                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
    #                                    [
    #                                        InlineKeyboardButton(text="Open in Tinkoff",
    #                                                             url=f'https://www.tinkoff.ru/invest/stocks/{ticker}')
    #                                    ],
    #                                ]))

    await query.message.edit_text(text=new_text, reply_markup=markup)

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

async def subscription_approve(query: CallbackQuery):
    user: User = await user_add_or_update(query, role='user', module=__name__)
    db_session = query.bot.get('db')
    document_title='dogovoroferti'
    document = await Document.get_document_by_title(db_session=db_session,title=document_title)
    await query.message.answer_document(document=document.file_id)
    await query.message.edit_text(
        text=f'❗️Ознакомьтесь с условиями договора перед тем как перейти к оплате:❗️',
        reply_markup=sub_approve_keyboard())

async def subscription_edit(query: CallbackQuery):
    user: User = await user_add_or_update(query, role='user', module=__name__)
    db_session = query.bot.get('db')
    subscription_products: Product = await Product.get_product_like_payload(db_session=db_session, payload='subscription')
    for subscription_product in subscription_products:
        payload = subscription_product.payload
        title = subscription_product.title
        description = subscription_product.description
        currency = subscription_product.currency
        price = float(subscription_product.price)
        ammount_labaledPrice = int(price * 100.00)

        provider_data = {
            "receipt": {
                "items": [
                    {
                        "description": description,
                        "quantity": "1.00",
                        "amount": {
                            "value": price,
                            "currency": currency
                        },
                        "vat_code": "2",
                    }
                ]
            }
        }

        ykassa_invoice = Ykassa_payment(title=title,
                                        description=description,
                                        currency=currency,
                                        prices=[
                                            LabeledPrice(
                                                label="subscription",
                                                amount=ammount_labaledPrice
                                            )
                                        ],
                                        provider_data=provider_data,
                                        start_parameter="create_invoice_sosisochnyi",
                                        need_email=True,
                                        send_email_to_provider=True
                                        )
        message = await query.bot.send_invoice(query.from_user.id,
                                     **ykassa_invoice.generate_invoice(),
                                     payload=payload+'__ykassa_telegram')


##### ТЕСТОВЫЙ ПЛАТЁЖ
    if user.role == 'tester':
        testpayment_products: Product = await Product.get_product_like_payload(db_session=db_session, payload='testpayment')
        for testpayment_product in testpayment_products:
            payload = testpayment_product.payload
            title = testpayment_product.title
            description = testpayment_product.description
            currency = testpayment_product.currency
            price = float(testpayment_product.price)
            ammount_labaledPrice = int(price * 100.00)

            provider_data = {
                "receipt": {
                    "items": [
                        {
                            "description": description,
                            "quantity": "1.00",
                            "amount": {
                                "value": price,
                                "currency": currency
                            },
                            "vat_code": "2",
                        }
                    ]
                }
            }

            ykassa_invoice_test = Ykassa_payment(title=title,
                                            description=description,
                                            currency=currency,
                                            prices=[
                                                LabeledPrice(
                                                    label="testpayment",
                                                    amount=ammount_labaledPrice
                                                )
                                            ],
                                            provider_data=provider_data,
                                            start_parameter="create_invoice_sosisochnyi_test",
                                            need_email=True,
                                            send_email_to_provider=True
                                            )
            message = await query.bot.send_invoice(query.from_user.id,
                                         **ykassa_invoice_test.generate_invoice(),
                                         payload=payload+'__ykassa_telegram')

        # message_id = message.message_id
        # chat_id = message.chat.id
        # await query.bot.delete_message()

    # payload = 'subscription__1__month'
    # title = 'Подписка на 1 месяц'
    # description = 'Подписка на 1 месяц на канал SosisochniePrognozi'
    # currency = 'RUB'
    # price = 100.00
    # ammount_labaledPrice = int(price * 100.00)
    #
    # provider_data = {
    #     "receipt": {
    #         "items": [
    #             {
    #                 "description": description,
    #                 "quantity": "1.00",
    #                 "amount": {
    #                     "value": price,
    #                     "currency": currency
    #                 },
    #                 "vat_code": "2",
    #             }
    #         ]
    #     }
    # }
    #
    # ykassa_invoice = Ykassa_payment(title=title,
    #                                 description=description,
    #                                 currency=currency,
    #                                 prices=[
    #                                     LabeledPrice(
    #                                         label="subscription",
    #                                         amount=ammount_labaledPrice
    #                                     )
    #                                 ],
    #                                 provider_data=provider_data,
    #                                 start_parameter="create_invoice_sosisochnyi",
    #                                 need_email=True,
    #                                 send_email_to_provider=True
    #                                 )
    # await query.bot.send_invoice(query.from_user.id,
    #                              **ykassa_invoice.generate_invoice(),
    #                              payload=payload+'__ykassa_telegram')
    #
    # await query.bot.send_invoice(query.from_user.id,
    #                              **Ykassa_1month.generate_invoice(),
    #                              payload="subscription__1__month__ykassa")
    # await query.bot.send_invoice(query.from_user.id,
    #                              **Ykassa_2month.generate_invoice(),
    #                              payload="subscription__2__month__ykassa")
    # await query.bot.send_invoice(query.from_user.id,
    #                              **Ykassa_3month.generate_invoice(),
    #                              payload="subscription__3__month__ykassa")
    await query.answer()

async def process_pre_checkout_query(query: PreCheckoutQuery):
    # await query.bot.send_message(chat_id=query.from_user.id, text="Спасибо за подписку!")
    payload_check = '__'.join(query.invoice_payload.split(sep="__")[:-1]) #получаем payload но без последней части после '__'/ тоесть ровно так, как должно быть в БД
    db_session = query.bot.get('db')
    check_products: Product = await Product.get_product_like_payload(db_session=db_session, payload=f'{payload_check}')

    test_product = []
    for check_product in check_products:
        test_product.append(check_product)
    if not test_product:
        await query.bot.answer_pre_checkout_query(pre_checkout_query_id=query.id, ok=False,
                                                  error_message='Такого продукта уже нет в прайсе. Загрузите Прайс еще раз')
        await query.bot.send_message(chat_id=query.from_user.id,
                                     text="Такого продукта уже нет в прайсе. Загрузите Прайс еще раз")
        return
    if len(test_product) == 1:
        test_product = test_product[0]
    if float(query.total_amount/100) == float(test_product.price):
        await query.bot.answer_pre_checkout_query(pre_checkout_query_id=query.id, ok=True)
    else:

        await query.bot.answer_pre_checkout_query(pre_checkout_query_id=query.id, ok=False,
                                                  error_message='Продукт не актуален. Загрузите Прайс еще раз')
        await query.bot.send_message(chat_id=query.from_user.id,
                                     text="Продукт не актуален. Загрузите Прайс еще раз")


    # await query.bot.answer_pre_checkout_query(pre_checkout_query_id=query.id, ok=True)
    #print(answer)


async def process_success_payment(query: SuccessfulPayment):
    user: User = await user_add_or_update(query, role='user', module=__name__)
    user_id = query.from_user.id
    db_session = query.bot.get('db')
    successful_payment = query.successful_payment
    currency = successful_payment.currency
    invoice_payload = successful_payment.invoice_payload
    payload_splited = invoice_payload.split(sep="__")
    if payload_splited[0] == 'subscription':
        ammount_sub = int(payload_splited[1])
        provider = payload_splited[3]
        provider_payment_charge_id = successful_payment.provider_payment_charge_id
        telegram_payment_charge_id = successful_payment.telegram_payment_charge_id
        total_amount = successful_payment.total_amount
        try:
            email = successful_payment.order_info.email
        except:
            email=None
        current_subscription = user.subscription_until
        if user.subscription_until > datetime.utcnow():
            new_subscription = user.subscription_until + relativedelta(months=ammount_sub)
        else:
            new_subscription = datetime.utcnow() + relativedelta(months=ammount_sub)
        updated_user: User = await user.update_user(db_session=db_session,
                                                    subscription_until=new_subscription)
        keyboard_link = [[InlineKeyboardButton('🚀 Получить ссылку на канал', callback_data=user_callback.new(action='link'))],
                         [InlineKeyboardButton('Главное меню', callback_data=user_callback.new(action='main'))]]
        link_markup = InlineKeyboardMarkup(inline_keyboard=keyboard_link)
        await query.bot.send_message(chat_id=query.from_user.id, text="Спасибо за подписку! Нажмите на кнопку для получения ссылки на канал", reply_markup=link_markup)
        logger = logging.getLogger(__name__)
        logger.info(
            f'пользователь {user.telegram_id}, {user.username}, {user.first_name}, {email} произвёл оплату на {float(total_amount)/100} {currency} за {invoice_payload}')
        updated_user: User = await User.get_user(db_session=db_session, telegram_id=user_id)

        paymentinfo: PaymentInfo = await PaymentInfo.add_paymentinfo(db_session=db_session,
                                          user_id=user_id,
                                          email=email,
                                          provider=provider,
                                          provider_payment_charge_id=provider_payment_charge_id,
                                          telegram_payment_charge_id=telegram_payment_charge_id,
                                          invoice_payload=invoice_payload,
                                          total_amount=float(total_amount/100),
                                          currency=currency)
        getpaymentinfo: PaymentInfo = await PaymentInfo.get_paymentinfo_by_charge_id_provider(db_session=db_session,
                                                                                              provider_payment_charge_id=provider_payment_charge_id, provider=provider)

    elif payload_splited[0] == 'testpayment':
        await query.bot.send_message(chat_id=query.from_user.id,
                                     text="Вы произвели тестовую оплату. платёж прошел успешно")
        logger = logging.getLogger(__name__)
        logger.info(
            f'тестовый пользователь {user.telegram_id}, {user.username}, {user.first_name} произвёл ТЕСТОВУЮ ОПЛАТУ')


async def successful_payment(message: Message):
    print(message)
    print(message.__dict__)


async def get_channel_invitelink(query: CallbackQuery):
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
            f"Здравствуйте! \nВаша подписка истекла. Обновите подписку для получения ссылки на канал.",
    reply_markup=first_menu_keyboard())
    elif user.is_member == True:
        await query.message.answer(
            f"Здравствуйте! \nВы уже являетесь подписчиком канала.")
    else:
        invite_link = await query.bot.create_chat_invite_link(chat_id=config.tg_bot.channel_id,
                                                                expire_date=timedelta(hours=1))
        await query.message.answer(f"Здравствуйте! \nВаша ссылка для входа в канал: {invite_link.invite_link}")


async def get_chat_invitelink(query: CallbackQuery):
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
            f"Здравствуйте! \nВаша подписка истекла. Обновите подписку для получения ссылки на канал.",
    reply_markup=first_menu_keyboard())
    elif user.is_private_group_member == True:
        await query.message.answer(
            f"Здравствуйте! \nВы уже являетесь подписчиком группы.")
    else:
        invite_link = await query.bot.create_chat_invite_link(chat_id=config.tg_bot.private_group_id,
                                                                expire_date=timedelta(hours=1))
        await query.message.answer(f"Здравствуйте! \nВаша ссылка для входа в приватный чат: {invite_link.invite_link}")


async def user_info(message: Message):
    user: User = await user_add_or_update(message, role='user', module=__name__)
    await message.answer(
            f'''Добро пожаловать в Сосисочные ресурсы!

Отсюда вы сможете попасть в канал с прогнозами, приватный чат для подписчиков, а так же получать актуальную информацию по текущим прогнозам, аналитикам и вашей подписке.

Для начала работы нажмите /menu
Если у вас возникнут вопросы в процессе пользования обратитесь к @sosisochniy_admin

В канале прогнозов обязательно ознакомьтесь с информацией в закреплённом сообщении. У вас есть бесплатная тестовая неделя чтобы освоиться (отсчет начинается с первого входа в бота).

Так же ждем вас в нашем бесплатном Сосисочном издании с самыми свежими новостями и обучающими статьями
https://t.me/SosisochnayaGazeta    
   ''')

async def user_start(message: Message):
    user: User = await user_add_or_update(message, role='user', module=__name__)
    await message.answer(
            f'''Добро пожаловать в Сосисочные ресурсы!

Отсюда вы сможете попасть в канал с прогнозами, приватный чат для подписчиков, а так же получать актуальную информацию по текущим прогнозам, аналитикам и вашей подписке.

Для начала работы нажмите /menu
Если у вас возникнут вопросы в процессе пользования обратитесь к @sosisochniy_admin

В канале прогнозов обязательно ознакомьтесь с информацией в закреплённом сообщении. У вас есть бесплатная тестовая неделя чтобы освоиться (отсчет начинается с первого входа в бота).

Так же ждем вас в нашем бесплатном Сосисочном издании с самыми свежими новостями и обучающими статьями
https://t.me/SosisochnayaGazeta
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
    # free = config.test.free
    # if free:
    #     subscription_until_str = config.test.free_subtime
    # else:
    #     subscription_until_str = config.test.prod_subtime
    #
    # subscription_until = datetime.strptime(subscription_until_str, '%d/%m/%y %H:%M:%S')



    logger = logging.getLogger(__name__)
    if status == 'member':
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
    dp.register_callback_query_handler(subscription_info, user_callback.filter(action='sub_info'), chat_type="private")
    dp.register_callback_query_handler(subscription_edit, user_callback.filter(action='sub_buy'), chat_type="private")
    dp.register_callback_query_handler(subscription_approve, user_callback.filter(action='sub_approve'), chat_type="private")
    dp.register_callback_query_handler(get_predict_list, user_callback.filter(action='pred'), state="*", chat_type="private")
    dp.register_callback_query_handler(get_predict_list, user_predict_callback.filter(action="back"), state="*",
                                       chat_type="private")
    dp.register_callback_query_handler(predict_info, user_predict_callback.filter(action="info"), state="*", chat_type="private")
    dp.register_callback_query_handler(list_analytics, user_callback.filter(action='analytic'), state="*", chat_type="private")
    dp.register_callback_query_handler(choose_analytic, user_list_analytic_callback.filter(), state="*", chat_type="private")
    dp.register_callback_query_handler(link_menu, user_callback.filter(action='link'), chat_type="private")
    dp.register_callback_query_handler(get_channel_invitelink, user_callback.filter(action='link_channel'), chat_type="private")
    dp.register_callback_query_handler(get_chat_invitelink, user_callback.filter(action='link_chat'), chat_type="private")
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
    dp.register_message_handler(user_info, commands=["info"], state="*", chat_type="private")
    dp.register_message_handler(process_success_payment, content_types = ContentType.SUCCESSFUL_PAYMENT)
