from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.utils.markdown import hcode


async def bot_echo(query: types.query):
    text = [
        "Эхо без состояния.",
        f"Сообщение:",
        query.text
    ]

    await query.answer('\n'.join(text))


async def bot_echo_all(query: types.query, state: FSMContext):
    state = await state.get_state()
    text = [
        f'Эхо в состоянии {hcode(state)}',
        f'Содержание сообщения:',
        hcode(state)
    ]
    await query.answer('\n'.join(text))


def register_echo(dp: Dispatcher):
    dp.register_query_handler(bot_echo)
    dp.register_query_handler(bot_echo_all, state="*", content_types=types.ContentTypes.ANY)
