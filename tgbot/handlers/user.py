from aiogram import Dispatcher
from aiogram.types import Message
from aiogram.types import ChatMemberUpdated


async def user_start(message: Message):
    user = message.from_user.username
    await message.reply(f"Hello, {user} ! \n /predict, чтобы создать прогноз")


async def chat_member_update(chat_member: ChatMemberUpdated):
    chat_member = chat_member.new_chat_member
    print(f'{chat_member} новый мембер')


def register_user(dp: Dispatcher):
    dp.register_message_handler(user_start, commands=["start"], state="*")
    dp.register_chat_member_handler(chat_member_update)
