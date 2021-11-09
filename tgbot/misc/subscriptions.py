from aiogram.types import LabeledPrice

from tgbot.misc.invoices import Ykassa_payment

Ykassa_1month = Ykassa_payment(title="1 Month Subscription",
                               description="buy subscription for 1 month",
                               currency='RUB',
                               prices=[
                                   LabeledPrice(
                                       label="1 month subscription",
                                       amount=10000
                                   )
                               ],
                               start_parameter="create_invoice_ykassa_1month",
                               need_email=True,
                               send_email_to_provider=True
)

Ykassa_2month = Ykassa_payment(title="2 Months Subscription",
                               description="buy subscription for 2 month",
                               currency='RUB',
                               prices=[
                                   LabeledPrice(
                                       label="2 month subscription",
                                       amount=19000
                                   )
                               ],
                               start_parameter="create_invoice_ykassa_2month",
)

Ykassa_3month = Ykassa_payment(title="3 Month Subscription",
                               description="buy subscription for 3 month",
                               currency='RUB',
                               prices=[
                                   LabeledPrice(
                                       label="3 month subscription",
                                       amount=28000
                                   )
                               ],
                               start_parameter="create_invoice_ykassa_3month",
)