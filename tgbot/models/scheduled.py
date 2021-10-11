import asyncio
import pprint

from aiogram import Bot

from tgbot.models.analytic import Analytic, Prediction
from tgbot.config import load_config
from tgbot.services.database import create_db_session


async def test_dbquery(bot):
    config = load_config()
    db_session = await create_db_session(config)
    predictions: list[Prediction] = await Prediction.get_active_predicts(db_session=db_session)
    print(f'объекты: {type(predictions)}')

    for prediction in predictions:
        print(f'объект: {type(prediction)}')
        pprint.pprint(prediction.__dict__)
        print(type(prediction.analytic))
        pprint.pprint(prediction.analytic.__dict__)
    # return predicts
    channel_id=config.tg_bot.channel_id
    await bot.send_message(chat_id=channel_id,
                                   text=f'Test scheduler')
    await bot

#asyncio.run(test_dbquery())
# print(type(predicts))
# #print(type(predicts))
# for predict in predicts:
#     print(type(predict))
#     print(predict['ticker'])