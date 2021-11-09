from dataclasses import dataclass
from typing import List
from tgbot.config import load_config, Config
from aiogram.types import LabeledPrice

from tgbot import config


@dataclass
class Ykassa_payment:
    title: str
    description: str
    start_parameter: str
    currency: str
    prices: List[LabeledPrice]
    provider_data: dict = None
    need_name: bool = False
    need_phone_number: bool = False
    need_email: bool = False
    need_shipping_address: bool = False
    send_phone_number_to_provider: bool = False
    send_email_to_provider: bool = False
    provider_token: str = load_config().misc.ykassa_token

    def generate_invoice(self):
        return self.__dict__
