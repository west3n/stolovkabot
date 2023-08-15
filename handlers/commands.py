from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext

from database import db_customer
from handlers.registration import individuals
from handlers import main_menu


async def get_id(msg: types.Message):
    if msg.photo and str(msg.from_id) in ['254465569', '15362825']:
        await msg.reply(msg.photo[-1].file_id)


async def bot_start(msg: types.Message, state: FSMContext):
    if msg.chat.type == "private":
        await state.finish()
        customer = await db_customer.get_customer(msg.from_id)
        if customer:
            await main_menu.main_menu_msg(msg)
        else:
            await individuals.start_registration(msg, msg.get_args(), state) if msg.get_args() \
                else await individuals.start_registration(msg, None, state)
    else:
        if msg.from_id in [254465569, 15362825]:
            await msg.answer("Привет, создатель!")
        else:
            await msg.answer("Не хочу с тобой общаться!")


def register(dp: Dispatcher):
    dp.register_message_handler(get_id, content_types=['photo'])
    dp.register_message_handler(bot_start, commands='start', state='*')
