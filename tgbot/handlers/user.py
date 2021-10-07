from aiogram import Dispatcher
from aiogram.types import Message


async def user_start(message: Message):
    user = message.from_user.username
    await message.reply(f"Hello, {user} ! \n /predict, чтобы создать прогноз")


def register_user(dp: Dispatcher):
    dp.register_message_handler(user_start, commands=["start"], state="*")
    dp.register_chat_member_handler()
