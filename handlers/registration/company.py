import re
import string
import random
import decouple

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.utils.exceptions import MessageToDeleteNotFound, MessageIdentifierNotSpecified

from database import db_company
from keyboards import inline, reply


class RegistrationCompany(StatesGroup):
    name = State()
    address = State()
    update = State()


def generate_key():
    characters = string.ascii_letters + string.digits
    key = ''.join(random.choice(characters) for _ in range(6))
    return key


async def registration_company_start(call: types.CallbackQuery, state: FSMContext):
    try:
        await call.message.delete()
    except MessageToDeleteNotFound:
        pass
    reg_start = await call.message.answer("💼 Напишите название компании:"
                                          "\n\n Например: ООО 'Ромашка'")
    await RegistrationCompany.name.set()
    await state.update_data({"reg_start": reg_start.message_id})


async def handle_company_name(msg: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            await msg.delete()
            await msg.bot.delete_message(msg.from_id, data.get('reg_start'))
    except (MessageToDeleteNotFound, MessageIdentifierNotSpecified):
        pass
    all_companies_names = await db_company.get_all_companies_names()
    if msg.text in all_companies_names:
        await msg.answer("❗️Компания с таким названием уже зарегистрирована!"
                         "\n Попробуйте зайти через уникальный ключ вашей компании или введите другое название, "
                         "если уверены, что компания точно не регистрировалась!")
    else:
        async with state.proxy() as data:
            data['name'] = msg.text
        name_msg = await msg.answer(f"🥳 Отлично! Название компании: {msg.text}"
                                    "\n\nТеперь нам нужен адрес для доставки:")
        await RegistrationCompany.next()
        await state.update_data({"name_msg": name_msg.message_id})


async def handle_company_address(msg: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            await msg.delete()
            await msg.bot.delete_message(msg.from_id, data.get('name_msg'))
    except (MessageToDeleteNotFound, MessageIdentifierNotSpecified):
        pass
    async with state.proxy() as data:
        data['address'] = msg.text
    await msg.answer(f"Адрес записан! Проверьте данные еще раз:\n\nИмя компании: "
                     f"{data.get('name')}\nАдрес:{data.get('address')}",
                     reply_markup=await inline.change_company_data_reg())
    await RegistrationCompany.next()


async def handle_company_update(call: types.CallbackQuery, state: FSMContext):
    if call.data == 'Всё верно, продолжаем регистрацию':
        async with state.proxy() as data:
            secret_key = generate_key()
            full_name = call.from_user.full_name
            special_chars = ['_', '.', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}']
            for char in special_chars:
                full_name = call.from_user.full_name.replace(char, '\\' + char)
            pattern = r'^[А-ЯЁ][а-яё]+\s[А-ЯЁ][а-яё]+$'
            if re.match(pattern, full_name):
                start_message = await call.message.edit_text(
                    f"Введите свои *Имя* и *Фамилию* \n\nНапример, '`{full_name}`'",
                    parse_mode=types.ParseMode.MARKDOWN_V2)
            else:
                start_message = await call.message.edit_text(f"Введите свои <b>Имя</b> и <b>Фамилию</b> "
                                                             f"\n\nНапример, Иван Иванов")
            company_id = await db_company.add_new_company(data, secret_key)
            data['start_message'] = start_message.message_id
            data['company_id'] = company_id
            await RegistrationCompany.next()
    else:
        pass


def register(dp: Dispatcher):
    dp.register_callback_query_handler(registration_company_start, text='Для компании')
    dp.register_message_handler(handle_company_name, state=RegistrationCompany.name)
    dp.register_message_handler(handle_company_address, state=RegistrationCompany.address)
    dp.register_callback_query_handler(handle_company_update, state=RegistrationCompany.update)
