from aiogram import Dispatcher, types
from database import db_customer
from handlers.registration import individuals


async def get_id(msg: types.Message):
    if msg.photo and str(msg.from_id) in ['254465569', '15362825']:
        await msg.reply(msg.photo[-1].file_id)


async def bot_start(msg: types.Message):
    customer = await db_customer.get_customer(msg.from_id)
    if msg.get_args():
        print(msg.get_args())
    else:
        if customer:
            await msg.answer("Здесь будет главное меню бота")
        else:
            await individuals.start_registration(msg)


def register(dp: Dispatcher):
    dp.register_message_handler(get_id, content_types=['photo'])
    dp.register_message_handler(bot_start, commands='start', state='*')
