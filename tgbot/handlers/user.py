import pprint
from datetime import datetime, timedelta

from aiogram import Dispatcher
from aiogram.types import Message
from aiogram.types import ChatMemberUpdated

from tgbot.filters.botfilters import flood_user_chat
from tgbot.misc import misc
from tgbot.models.users import User

async def testflood(message: Message):
    print(message.text)

async def myinfo(message: Message):
    user_id=message.from_user.id
    username=message.from_user.username
    await message.answer(text=f'user_id: {user_id}\n username: {username}')
        # await User.add_user(db_session=db_session,
        #               subscription_until=datetime.utcnow() + timedelta(days=1000),
        #               is
        #               )


def register_user(dp: Dispatcher):
    #dp.register_message_handler(testflood, state="*")
    #dp.register_message_handler(myinfo, commands=["testinfo"], state="*")
    dp.register_message_handler(myinfo, flood_user_chat, commands=["testinfo"], state="*")
