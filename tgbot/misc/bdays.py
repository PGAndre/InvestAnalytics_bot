import asyncio
from datetime import datetime, timedelta
import numpy as np
import pandas_market_calendars as mcal

# Create a calendar
from pandas import DatetimeIndex

# nyse = mcal.get_calendar('NYSE')
# holidays = nyse.holidays()
# dt2021 = np.datetime64(datetime(2021,1 ,1))
# for holiday in holidays.holidays:
#     if np.datetime64(datetime(2021,12,31)) > holiday > np.datetime64(datetime(2021,1 ,1)):
#         print(holiday)
#         print(type(holiday))
#
# day = datetime(2021,12,24)
# print(day)
#функция выдает Nй торговый день отсчитывая от start_day
async def next_business_day(start_day, business_days):
    nyse = mcal.get_calendar('NYSE')
    holidays = nyse.holidays().holidays
    ONE_DAY = timedelta(days=1)
    temp_day = start_day
    for i in range(0, business_days):
        next_day = temp_day + ONE_DAY
        now_holiday = np.datetime64(next_day.date())
        isholiday = now_holiday in holidays
        while next_day.weekday() in [5, 6] or np.datetime64(next_day.date()) in holidays:
            next_day += ONE_DAY
        temp_day = next_day
    print(temp_day)

    print(type(temp_day))
    return temp_day

async def count_tdays(start_day, last_day):
    nyse = mcal.get_calendar('NYSE')
    holidays = nyse.holidays().holidays
    ONE_DAY = timedelta(days=1)
    temp_day = start_day
    count = 0
    while temp_day < last_day:
        next_day = temp_day + ONE_DAY
        if next_day.weekday() in [5, 6] or np.datetime64(next_day.date()) in holidays:
            temp_day = next_day
            continue
        count += 1
        temp_day = next_day
    print(count)
    return count


asyncio.run(next_business_day(datetime.utcnow() + timedelta(days=-3), 4))
# asyncio.run(count_tdays(datetime.utcnow() + timedelta(days=-1), datetime.utcnow() + timedelta(days=+1)))


