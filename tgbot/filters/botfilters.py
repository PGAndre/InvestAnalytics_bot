from tgbot.config import Config


def from_user_chat(query):
    filter = query.message.chat.id == query.from_user.id
    return filter

def flood_user_chat(message):
    config: Config = message.bot.get('config')
    flood_channel_id=config.tg_bot.flood_channel_id
    filter = message.chat.id == flood_channel_id
    return filter