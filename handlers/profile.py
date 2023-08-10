import asyncio

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State

from keyboards import inline, reply
from aiogram.utils.exceptions import MessageToDeleteNotFound
from database import db_customer, db_company
from handlers import main_menu


class ChangePhone(StatesGroup):
    phone = State()


class ChangeAddress(StatesGroup):
    address = State()


async def handle_profile(call: types.CallbackQuery):
    user = await db_customer.get_customer(call.from_user.id)
    text = f"<b> 🪪 Ваш профиль</b>" \
           f"\n\n<b>Имя</b>: {user[2]}"
    try:
        company = await db_company.get_company_data(user[3])
        company = company[1]
    except TypeError:
        company = None
    text += f"\n<b>Компания:</b> {company}" if user[3] is not None else ""
    text += f"\n<b>Адрес доставки</b>: {user[4]}" \
            f"\n<b>Номер телефона:</b> {user[1]}" \
            f"\n\n<em>❔В этом меню вы можете изменить свои данные по кнопкам ниже, " \
            f"а также просмотреть свои заказы</em>"
    await call.message.edit_text(text, reply_markup=await inline.profile_menu(user[3]))


async def back_button(call: types.CallbackQuery):
    await main_menu.main_menu_call(call)


async def change_phone(call: types.CallbackQuery, state: FSMContext):
    try:
        await call.message.delete()
    except MessageToDeleteNotFound:
        pass
    phone_msg = await call.message.answer("Вы хотите изменить номер телефона. "
                                          "Пришлите новый номер в формате +79XXXXXXXXX/89XXXXXXXXX "
                                          "или нажмите кнопку ниже", reply_markup=await reply.contact())
    await ChangePhone.phone.set()
    await state.update_data({"phone_msg": phone_msg.message_id})


async def change_phone_finish(msg: types.Message, state: FSMContext):
    async with state.proxy() as data:
        try:
            await msg.delete()
            await msg.bot.delete_message(msg.from_id, data.get('phone_msg'))
        except MessageToDeleteNotFound:
            pass
        if msg.text:
            if msg.text.startswith('+7') or msg.text.startswith('7') or msg.text.startswith('8'):
                digits = msg.text.replace('+', '').replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
                if digits.isdigit() and len(digits) == 11:
                    await state.update_data({'phone': msg.text})
                    message = await msg.answer(f"Ваш номер телефона успешно обновлен!")
                    await db_customer.update_phone(msg.from_id, int(msg.text))
                    user = await db_customer.get_customer(msg.from_user.id)
                    text = f"<b> 🪪 Ваш профиль</b>" \
                           f"\n\n<b>Имя</b>: {user[2]}"
                    try:
                        company = await db_company.get_company_data(user[4])
                        company = company[1]
                    except TypeError:
                        company = None
                    text += f"\n<b>Компания:</b> {company}" if user[3] is not None else ""
                    text += f"\n<b>Адрес доставки</b>: {user[4]}" \
                            f"\n<b>Номер телефона:</b> {msg.text}" \
                            f"\n\n<em>❔В этом меню вы можете изменить свои данные по кнопкам ниже, " \
                            f"а также просмотреть свои заказы</em>"
                    await msg.answer(text, reply_markup=await inline.profile_menu(user[4]))
                    await msg.bot.delete_message(msg.from_id, message.message_id)
                    await state.finish()
                else:
                    wrong_format = await msg.answer(
                        "❌ Количество цифр в телефоне не может быть меньше 11, попробуйте еще раз!")
                    data['wrong_format_1'] = wrong_format.message_id
            else:
                wrong_format = await msg.answer(
                    "❌ Формат номера телефона должен быть +79180000000 или 89180000000, попробуйте еще раз!")
                data['wrong_format_2'] = wrong_format.message_id
        elif msg.contact:
            await state.update_data({'phone': msg.contact.phone_number})
            message = await msg.answer(f"Ваш номер телефона успешно обновлен!")
            await db_customer.update_phone(msg.from_id, msg.contact.phone_number)
            user = await db_customer.get_customer(msg.from_user.id)
            text = f"<b> 🪪 Ваш профиль</b>" \
                   f"\n\n<b>Имя</b>: {user[2]}"
            try:
                company = await db_company.get_company_data(user[3])
                company = company[1]
            except TypeError:
                company = None
            text += f"\n<b>Компания:</b> {company}" if user[3] is not None else ""
            text += f"\n<b>Адрес доставки</b>: {user[4]}" \
                    f"\n<b>Номер телефона:</b> {msg.contact.phone_number}" \
                    f"\n\n<em>❔В этом меню вы можете изменить свои данные по кнопкам ниже, " \
                    f"а также просмотреть свои заказы</em>"
            await msg.answer(text, reply_markup=await inline.profile_menu(user[3]))
            await msg.bot.delete_message(msg.chat.id, message.message_id)
            await state.finish()


async def change_address(call: types.CallbackQuery, state: FSMContext):
    address_msg = await call.message.edit_text("Вы хотите обновить адрес для доставки, пожалуйста напишите новый адрес:")
    await ChangeAddress.address.set()
    await state.update_data({"address_msg": address_msg.message_id})


async def change_address_finish(msg: types.Message, state: FSMContext):
    async with state.proxy() as data:
        try:
            await msg.delete()
            await msg.bot.delete_message(msg.from_id, data.get('address_msg'))
        except MessageToDeleteNotFound:
            pass
    await db_customer.update_address(msg.from_id, msg.text)
    message = await msg.answer("Ваш адрес для доставки успешно обновлен!")
    user = await db_customer.get_customer(msg.from_user.id)
    text = f"<b> 🪪 Ваш профиль</b>" \
           f"\n\n<b>Имя</b>: {user[2]}"
    try:
        company = await db_company.get_company_data(user[3])
        company = company[1]
    except TypeError:
        company = None
    text += f"\n<b>Компания:</b> {company}" if user[3] is not None else ""
    text += f"\n<b>Адрес доставки</b>: {msg.text}" \
            f"\n<b>Номер телефона:</b> {user[1]}" \
            f"\n\n<em>❔В этом меню вы можете изменить свои данные по кнопкам ниже, " \
            f"а также просмотреть свои заказы</em>"
    await msg.answer(text, reply_markup=await inline.profile_menu(user[3]))
    await msg.bot.delete_message(msg.from_id, message.message_id)
    await state.finish()


def register(dp: Dispatcher):
    dp.register_callback_query_handler(handle_profile, text="Мой профиль")
    dp.register_callback_query_handler(back_button, text="Главное меню")
    dp.register_callback_query_handler(change_phone, text="Изменить номер телефона")
    dp.register_message_handler(change_phone_finish, content_types=['text', 'contact'], state=ChangePhone.phone)
    dp.register_callback_query_handler(change_address, text="Изменить адрес доставки")
    dp.register_message_handler(change_address_finish, state=ChangeAddress.address)
