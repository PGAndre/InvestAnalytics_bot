from tgbot.config import Config


def from_user_chat(query):
    filter = query.message.chat.id == query.from_user.id
    return filter

async def flood_user_chat(message):
    config: Config = message.bot.get('config')
    flood_channel_id=config.tg_bot.flood_channel_id
    filter = message.chat.id == flood_channel_id
    return filter

async def channel_chat_member(chat_member):
    config = chat_member.bot.get('config')
    filter = chat_member.chat.id == config.tg_bot.channel_id
    return filter

async def group_chat_member(chat_member):
    config = chat_member.bot.get('config')
    filter =  chat_member.chat.id == config.tg_bot.group_id
    return filter