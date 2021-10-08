from tgbot.config import Config
from tgbot.models.analytic import Analytic
from tgbot.services.database import create_db_session


async def check(obj):
    config: Config = obj.bot.get('config')
    db_session = await create_db_session(config)
    analytics = await Analytic.get_active_analytics(db_session=db_session)
    listof_analytics = []
    for analytic in analytics:
        listof_analytics.append(analytic.telegram_id)
    print(listof_analytics)
    # return obj.from_user.id in config.tg_bot.analytic_ids
    return obj.from_user.id in listof_analytics