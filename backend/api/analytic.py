import json
from pprint import pprint
from typing import List

import redis as redis
from sqlalchemy.ext.asyncio import AsyncSession

import fastapi as _fastapi
from fastapi.encoders import jsonable_encoder
from backend.schemas import analytic as _analytic
from backend.services.base import get_redis_client
from tgbot.config import load_config
from tgbot.models.analytic import Analytic
from tgbot.services.database import get_session
from backend.services import analytic as _services_Analytic

router = _fastapi.APIRouter()

config = load_config(".env")
redis_host = config.redis.host
redis_port = config.redis.port
redis_password = config.redis.password
redis_client = redis.Redis(host=redis_host, port = redis_port, password=redis_password)

@router.get("/analytics/", response_model=List[_analytic.Analytic])
async def get_all_analytics(session: AsyncSession = _fastapi.Depends(get_session),
                            redis_client = _fastapi.Depends(get_redis_client)):
    # analytics = await _services_Analytic.get_all_analytics(db_session=session)
    analytics = await Analytic.get_all_analytics(db_session=session)
    my_object = _analytic.Analytic.from_orm(analytics[0])
    # data = my_object.json()
    analytics_list = [_analytic.Analytic.from_orm(analytic).json() for analytic in analytics]
    # json_analytics = jsonable_encoder(analytics)
    # analytics_list = list(map(json.dumps, json_analytics))
    # analytics_list = [json.dumps(analytic) for analytic in json_analytics]
    # analytics_list = []
    # for analytic in json_analytics:
    #     analytics_list.append(json.dumps(analytic))
    # for analytic in analytics:
    #     print(analytic.__dict__)
    #     analytics_list.append(json.dumps(analytic.__dict__, default=str))
    await redis_client.set('foo', 'bar')
    await redis_client.expire('foo', 100)
    foo = await redis_client.get('foo')
    print(foo)
    # print(analytics_list[0])
    # analytic = analytics_list[0]
    # d = dict(analytic)
    d = analytics_list
    print(type(d))
    # redis_client.lpush('analytics', *json_analytics)
    await redis_client.lpush('fet', *d)
    await redis_client.expire('fet', 10)
    get_all_analytics = await redis_client.lrange('fet', 0, -1)
    # analytics = []
    analytics = [json.loads(analytic) for analytic in get_all_analytics]
    # for analytic in get_all_analytics:
    #     analytics.append(json.loads(analytic))
    #     print(analytics[0])
    print(type(get_all_analytics))
    print(get_all_analytics)
    # redis_client.close()
    return analytics

@router.get("/analyticsusers/", response_model=List[_analytic.AnalyticPublic])
async def get_all_analytics(session: AsyncSession = _fastapi.Depends(get_session)):
    # analytics = await _services_Analytic.get_all_analytics(db_session=session)

    analytics = [
        {
            "Nickname": "Kane",
            "telegram_id": 402626302,
            "description": "торгую почти два года, стиль: скальпинг, трейдинг внутри дня, краткосрочные сделки как правило не больше 2ух недель",
            "predicts_total": 69,
            "rating": 63.29,
            "is_active": True
        },
        {
            "Nickname": "AlekseyTrifonov",
            "telegram_id": 1061599177,
            "description": "Работал 6 дней в неделю на Абрамовича, покинул компанию, чтобы работать 7 дней 😅",
            "predicts_total": 63,
            "rating": 56.01,
            "is_active": True
        },
        {
            "Nickname": "Banana",
            "telegram_id": 5121505134,
            "description": "Вожделенный миньонами фрукт, обретший самосознание. Долго скитался, пока не открыл в себе талант биржевого аналитика.",
            "predicts_total": 196,
            "rating": 57.68,
            "is_active": True
        },
        {
            "Nickname": "VF",
            "telegram_id": 1212205332,
            "description": "Если я прав, то зарабатываю, ошибаюсь - теряю деньги. Это ли не мечта человека, который хочет всего добиться сам?)) ",
            "predicts_total": 216,
            "rating": 63.92,
            "is_active": True
        },
        {
            "Nickname": "loriko",
            "telegram_id": 343311669,
            "description": "Поднимем деньжат на новостях и ожиданиях? Здесь только краткосрок, для долгосрока - пульс: loriko",
            "predicts_total": 152,
            "rating": 62.45,
            "is_active": True
        },
        {
            "Nickname": "BavarskayaSosisochka",
            "telegram_id": 1905958275,
            "description": "Та самая Сосиска",
            "predicts_total": 44,
            "rating": 100,
            "is_active": True
        }
    ]
    return analytics
