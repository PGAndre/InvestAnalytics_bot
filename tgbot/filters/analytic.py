import typing

from aiogram.dispatcher.filters import BoundFilter

from tgbot.config import Config
from tgbot.models.analytic import Analytic
from tgbot.services.database import create_db_session


class AnalyticFilter(BoundFilter):
    key = 'is_analytic'

    def __init__(self, is_analytic: typing.Optional[bool] = None):
        self.is_analytic = is_analytic

    async def check(self, obj):
        if self.is_analytic is None:
            return True
        config: Config = obj.bot.get('config')
        db_session = await create_db_session(config)
        analytics = await Analytic.get_active_analytics(db_session=db_session)
        listof_analytics = []
        for analytic in analytics:
            listof_analytics.append(analytic.telegram_id)
        print(listof_analytics)
        # return obj.from_user.id in config.tg_bot.analytic_ids
        return obj.from_user.id in listof_analytics
