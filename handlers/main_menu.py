from aiogram import Dispatcher, types
from keyboards import inline
from aiogram.utils.exceptions import MessageToEditNotFound


async def main_menu_msg(msg: types.Message):
    await msg.answer("Выберите один из вариантов:", reply_markup=await inline.main_menu(msg.from_id))


async def main_menu_call(call: types.CallbackQuery):
    try:
        await call.message.edit_text("Выберите один из вариантов:", reply_markup=await inline.main_menu(call.from_user.id))
    except MessageToEditNotFound:
        await call.message.delete()
        await call.message.answer("Выберите один из вариантов:", reply_markup=await inline.main_menu(call.from_user.id))
