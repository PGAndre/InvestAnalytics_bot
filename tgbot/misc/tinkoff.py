import asyncio
from datetime import datetime, timedelta

import tinvest
import pprint

from tinvest import CandleResolution, Candles

from tgbot.config import Config


async def search_by_ticker(ticker: str, config: Config):
    tcs_token = config.misc.tcs_token
    client = tinvest.AsyncClient(tcs_token)
    ticker = await client.get_market_search_by_ticker(ticker)
    await client.close()
    # pprint.pprint(ticker.__dict__)
    if len(ticker.payload.instruments) != 0:
        name = ticker.payload.instruments[0].name
        figi = ticker.payload.instruments[0].figi
        currency = ticker.payload.instruments[0].currency
        return {'name': name, 'figi': figi, 'currency': currency}
    else:
        return ticker.payload.instruments
    # pprint.pprint(ticker)
    # return len(ticker.payload.instruments) == 0


async def search_by_ticker_test(ticker: str):
    client = tinvest.AsyncClient(token)
    ticker = await client.get_market_search_by_ticker(ticker)
    await client.close()
    # pprint.pprint(ticker.__dict__)
    # print(len(ticker.payload.instruments) != 0)
    if len(ticker.payload.instruments) != 0:
        name = ticker.payload.instruments[0].name
        figi = ticker.payload.instruments[0].figi
        currency = ticker.payload.instruments[0].currency
        return {'name': name, 'figi': figi, 'currency': currency}
    else:
        return ticker.payload.instruments

#общая функция получения свечей по figi за определённый период
async def get_market_candles(figi: str,
                             from_: datetime,
                             to: datetime,
                             interval: CandleResolution, config: Config) -> Candles:
    tcs_token = config.misc.tcs_token
    client = tinvest.AsyncClient(tcs_token)
    candles = await client.get_market_candles(figi, from_, to, interval)
    #print(type(candles.payload))
    #print(candles.payload)
    # for candle in candles:
    #     print(type(candle[1]))
    #     print(candle[1])
    # print(candles.payload.candles[0].o)
    #pprint.pprint(candles.payload)
    await client.close()
    return candles.payload
    #return candles

# получить текущую стоимость по figi
async def get_latest_cost(figi: str, config: Config, *args):
    nowtime = datetime.utcnow()
    fromtime = datetime.utcnow() - timedelta(hours=3)
    candles: Candles = await get_market_candles(figi=figi, from_=fromtime, to=nowtime, interval=CandleResolution.min1, config=config)
    # print(candles)
    if not candles.candles:
        fromtime = datetime.utcnow() - timedelta(hours=10)
        candles: Candles = await get_market_candles(figi=figi, from_=fromtime, to=nowtime,
                                                    interval=CandleResolution.min10, config=config)
        if not candles.candles:
            fromtime = datetime.utcnow() - timedelta(hours=100)
            candles: Candles = await get_market_candles(figi=figi, from_=fromtime, to=nowtime,
                                                        interval=CandleResolution.hour, config=config)
    # count = 0
    # for candle in candles.candles:
    #     pprint.pprint(candle)
    #     count = count+1
    #     print(count)
    # print(count)
    # print(type(candles.candles))
    # print(max(candle.h for candle in candles.candles))
    # print(max(candles.candles, key=lambda item: item.h))  # среди всех объектов свечей выдаёт ту, у которой значение h(high price) максимально
    return candles.candles[-1].c

async def get_latest_cost_history(figi: str, config: Config, to_time: datetime):
    to_time = to_time
    fromtime = to_time - timedelta(hours=3)
    candles: Candles = await get_market_candles(figi=figi, from_=fromtime, to=to_time, interval=CandleResolution.min1,
                                                config=config)
    # print(candles)
    if not candles.candles:
        fromtime = to_time - timedelta(hours=10)
        candles: Candles = await get_market_candles(figi=figi, from_=fromtime, to=to_time,
                                                    interval=CandleResolution.min10, config=config)
        if not candles.candles:
            fromtime = to_time - timedelta(hours=100)
            candles: Candles = await get_market_candles(figi=figi, from_=fromtime, to=to_time,
                                                        interval=CandleResolution.hour, config=config)
    # print(candles)
    count = 0
    # for candle in candles.candles:
    #     pprint.pprint(candle)
    #     count = count+1
    #     print(count)
    # print(count)
    # print(type(candles.candles))
    # print(max(candle.h for candle in candles.candles))
    # print(max(candles.candles, key=lambda item: item.h))  # среди всех объектов свечей выдаёт ту, у которой значение h(high price) максимально
    return candles.candles[-1].c

async def latestcost(figi: str, config: Config):
    tcs_token = config.misc.tcs_token
    client = tinvest.AsyncClient(tcs_token)
    OrderbookResponse = await client.get_market_orderbook(figi=figi, depth=1)
    latestcost = OrderbookResponse.payload.last_price
    await client.close()
    return latestcost
    # print(OrderbookResponse)


async def get_candles_inrange(figi: str, from_: datetime, to: datetime, interval: str, config: Config)  -> Candles:
    if interval == 'hour':
        interval = CandleResolution.hour
    if interval == 'day':
        interval = CandleResolution.day
    if interval == 'minute':
        interval = CandleResolution.min1

    candles: Candles = await get_market_candles(figi=figi, from_=from_, to=to, interval=interval, config=config)
    # print(candles)
    # count = 0
    # for candle in candles.candles:
    #     pprint.pprint(candle)
    #     count = count+1
    #     print(count)
    # print(count)
    # print(type(candles.candles))
    # print(max(candle.h for candle in candles.candles))
    # maxcandle = max(candles.candles, key=lambda item: item.h)
    # print(maxcandle)
    return candles



#print(asyncio.run(search_by_ticker_test(ticker='AAPLdfgd')))
# nowtime = datetime.utcnow()
# fromtime = datetime.utcnow() - timedelta(seconds=350)
# pprint.pprint(nowtime)
# pprint.pprint(fromtime)
#pprint.pprint(asyncio.run(get_latest_cost('BBG005DXJS36')))

##tofix: добавить возможность загружать конфиг напрямую в этот модуль!
