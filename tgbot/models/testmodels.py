import asyncio
import pprint
from datetime import datetime

from sqlalchemy import update

from tgbot.models.analytic import Analytic, Prediction
from tgbot.config import load_config
from tgbot.services.database import create_db_session


async def test_dbquery():
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

async def test_dbupdate():
    config = load_config()
    db_session = await create_db_session(config)
    await Prediction.update_predict(db_session, end_value=200.00, end_date=datetime.now(), id=4)
#     async with db_session() as db_session:
#         sql = update(Prediction).where(Prediction.id == 5).values(end_date=datetime.now(), end_value=200)
#         print(sql)
#         await db_session.execute(sql)
#         await db_session.commit()

# async def add_analytic():
#     config = load_config()
#     db_session = await create_db_session(config)
#     analytic = await Analytic.add_analytic(db_session, telegram_id=209811569)
#     print(f'создан новый аналитик: {type(analytic)}, {analytic}, {analytic.__dict__}')
# #     async with db_session() as db_session:
# #         sql = update(Prediction).where(Prediction.id == 5).values(end_date=datetime.now(), end_value=200)
# #         print(sql)
# #         await db_session.execute(sql)
# #         await db_session.commit()

# asyncio.run(add_analytic())
# print(type(predicts))
# #print(type(predicts))
# for predict in predicts:
#     print(type(predict))
#     print(predict['ticker'])