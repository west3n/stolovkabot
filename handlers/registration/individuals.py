import re
import decouple

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.utils.exceptions import MessageToDeleteNotFound, MessageIdentifierNotSpecified

from database import db_customer
from keyboards import inline, reply


class RegistrationUser(StatesGroup):
    name = State()
    address = State()
    phone = State()
    confirm = State()
    update = State()


async def start_registration(msg: types.Message):
    await msg.answer_photo(photo=decouple.config("START_REGISTRATION"),
                           caption=f"{msg.from_user.first_name}, добро пожаловать в <b>Classic Food!</b> 🙋"
                                   f"\n\nВыберите тип регистрации для доставки комплексных обедов:",
                           reply_markup=await inline.first_choice())


async def registration_individual_start(call: types.CallbackQuery, state: FSMContext):
    try:
        await call.message.delete()
    except MessageToDeleteNotFound:
        pass
    full_name = call.from_user.full_name
    special_chars = ['_', '.', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}']
    for char in special_chars:
        full_name = call.from_user.full_name.replace(char, '\\' + char)
    pattern = r'^[А-ЯЁ][а-яё]+\s[А-ЯЁ][а-яё]+$'
    if re.match(pattern, full_name):
        start_message = await call.message.answer(f"Введите свои *Имя* и *Фамилию* \n\nНапример, '`{full_name}`'",
                                                  parse_mode=types.ParseMode.MARKDOWN_V2)
    else:
        start_message = await call.message.answer(f"Введите свои <b>Имя</b> и <b>Фамилию</b> "
                                                  f"\n\nНапример, Иван Иванов")
    await RegistrationUser.name.set()
    async with state.proxy() as data:
        data['start_message'] = start_message.message_id


async def handle_individual_name(msg: types.Message, state: FSMContext):
    pattern = r'^[А-ЯЁ][а-яё]+\s[А-ЯЁ][а-яё]+$'
    if not re.match(pattern, msg.text):
        await msg.delete()
        alarm_message = await msg.answer("❌ Пожалуйста, введите своё имя в формате Имя Фамилия на <b>русском языке</b>")
        async with state.proxy() as data:
            data['alarm_message'] = alarm_message.message_id
    else:
        async with state.proxy() as data:
            data['name'] = msg.text
            try:
                await msg.delete()
            except (MessageToDeleteNotFound, MessageIdentifierNotSpecified):
                pass
            try:
                await msg.bot.delete_message(msg.chat.id, data.get('start_message'))
            except (MessageToDeleteNotFound, MessageIdentifierNotSpecified):
                pass
            try:
                await msg.bot.delete_message(msg.chat.id, data.get('alarm_message'))
            except (MessageToDeleteNotFound, MessageIdentifierNotSpecified):
                pass
            address_message = await msg.answer(
                f'Ок, {data.get("name")}, продолжаем регистрацию.'
                f'\n\n🍔 Теперь введите адрес, куда нужно доставлять еду (адрес позже можно изменить):'
                f'\n\n🏢 Например, Литейный проспект, 4, офис 228')
            data['address_message'] = address_message.message_id
            await RegistrationUser.next()


async def handle_individual_address(msg: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['address'] = msg.text
        try:
            await msg.delete()
        except (MessageToDeleteNotFound, MessageIdentifierNotSpecified):
            pass
        try:
            await msg.bot.delete_message(msg.chat.id, data.get('address_message'))
        except (MessageToDeleteNotFound, MessageIdentifierNotSpecified):
            pass
        phone_message = await msg.answer(
            f"{data.get('name')}, я сохранил ваш адрес:\n{data.get('address')}"
            f"\n\nТеперь введите номер телефона (в формате +79180000000 или 89180000000) или нажмите кнопку ниже:",
            reply_markup=await reply.contact())
        data['phone_message'] = phone_message.message_id
    await RegistrationUser.next()


async def handle_individual_phone(msg: types.Message, state: FSMContext):
    if msg.text:
        if msg.text.startswith('+7') or msg.text.startswith('7') or msg.text.startswith('8'):
            digits = msg.text.replace('+', '').replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
            if digits.isdigit() and len(digits) == 11:
                async with state.proxy() as data:
                    data['phone'] = msg.text
                    try:
                        await msg.delete()
                    except (MessageToDeleteNotFound, MessageIdentifierNotSpecified):
                        pass
                    try:
                        await msg.bot.delete_message(msg.chat.id, data.get('phone_message'))
                    except (MessageToDeleteNotFound, MessageIdentifierNotSpecified):
                        pass
                    try:
                        await msg.bot.delete_message(msg.chat.id, data.get('wrong_format_1'))
                    except (MessageToDeleteNotFound, MessageIdentifierNotSpecified):
                        pass
                    try:
                        await msg.bot.delete_message(msg.chat.id, data.get('wrong_format_2'))
                    except (MessageToDeleteNotFound, MessageIdentifierNotSpecified):
                        pass
                    await msg.answer("Отлично! Проверим ваши данные:"
                                     f"\n\n<b>Имя:</b> <em>{data.get('name')}</em>"
                                     f"\n<b>Адрес доставки:</b> <em>{data.get('address')}</em>"
                                     f"\n<b>Номер телефона:</b> <em>{data.get('phone')}</em>"
                                     f"\n\nДанные верны?",
                                     reply_markup=await inline.confirm_individual_registration())
                    await RegistrationUser.next()
            else:
                await msg.delete()
                wrong_format = await msg.answer(
                    "❌ Количество цифр в телефоне не может быть меньше 11, попробуйте еще раз!")
                async with state.proxy() as data:
                    data['wrong_format_1'] = wrong_format.message_id
        else:
            await msg.delete()
            wrong_format = await msg.answer(
                "❌ Формат номера телефона должен быть +79180000000 или 89180000000, попробуйте еще раз!")
            async with state.proxy() as data:
                data['wrong_format_2'] = wrong_format.message_id
    elif msg.contact:
        async with state.proxy() as data:
            data['phone'] = msg.contact.phone_number
        try:
            await msg.delete()
        except (MessageToDeleteNotFound, MessageIdentifierNotSpecified):
            pass
        try:
            await msg.bot.delete_message(msg.chat.id, data.get('phone_message'))
        except (MessageToDeleteNotFound, MessageIdentifierNotSpecified):
            pass
        try:
            await msg.bot.delete_message(msg.chat.id, data.get('wrong_format_1'))
        except (MessageToDeleteNotFound, MessageIdentifierNotSpecified):
            pass
        try:
            await msg.bot.delete_message(msg.chat.id, data.get('wrong_format_2'))
        except (MessageToDeleteNotFound, MessageIdentifierNotSpecified):
            pass
        await msg.answer("Отлично! Проверим ваши данные:"
                         f"\n\n<b>Имя:</b> <em>{data.get('name')}</em>"
                         f"\n<b>Адрес доставки:</b> <em>{data.get('address')}</em>"
                         f"\n<b>Номер телефона:</b> <em>{data.get('phone')}</em>"
                         f"\n\nДанные верны?",
                         reply_markup=await inline.confirm_individual_registration())
        await RegistrationUser.next()


async def handle_individual_confirm(call: types.CallbackQuery, state: FSMContext):
    if call.data == "Назад":
        async with state.proxy() as data:
            await call.message.edit_text(
                "Проверим ваши данные еще раз:"
                f"\n\n<b>Имя:</b> <em>{data.get('name')}</em>"
                f"\n<b>Адрес доставки:</b> <em>{data.get('address')}</em>"
                f"\n<b>Номер телефона:</b> <em>{data.get('phone')}</em>"
                f"\n\nДанные верны?",
                reply_markup=await inline.confirm_individual_registration())
    elif call.data == 'Да':
        await call.message.edit_text(
            "Данные успешно сохранены, теперь перейдем к составлению комплексного обеда."
            "\n\n<em>Вы всегда сможете изменить номер телефона и адрес доставки в 'Профиле'</em>")
        async with state.proxy() as data:
            await db_customer.insert_individual_customer(data, call.from_user.id)
        await state.finish()
    elif call.data == "Нет":
        await call.message.edit_text("Какой из параметров вы хотите изменить?",
                                     reply_markup=await inline.change_individual_data_reg())
    else:
        if call.data == 'Номер':
            await call.message.delete()
            new_data_message = await call.message.answer(
                f"Вы хотите изменить {call.data}. "
                f"Введите новые данные или нажмите кнопку ниже:",
                reply_markup=await reply.contact())
            async with state.proxy() as data:
                data['new_data_message'] = new_data_message.message_id
        else:
            new_data_message = await call.message.edit_text(f"Вы хотите изменить {call.data}. Введите новые данные:")
            async with state.proxy() as data:
                data['new_data_message'] = new_data_message.message_id
        async with state.proxy() as data:
            data['update'] = call.data
        await RegistrationUser.next()


async def handle_individual_update(msg: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if data.get('update') == "Номер":
            if msg.text:
                if msg.text.startswith('+7') or msg.text.startswith('7') or msg.text.startswith('8'):
                    digits = msg.text.replace('+', '').replace(' ', '').replace('-', '').replace('(', '').replace(')',
                                                                                                                  '')
                    if digits.isdigit() and len(digits) == 11:
                        await state.update_data({'phone': msg.text})
                        try:
                            await msg.delete()
                        except (MessageToDeleteNotFound, MessageIdentifierNotSpecified):
                            pass
                        try:
                            await msg.bot.delete_message(msg.chat.id, data.get('phone_message'))
                        except (MessageToDeleteNotFound, MessageIdentifierNotSpecified):
                            pass
                        try:
                            await msg.bot.delete_message(msg.chat.id, data.get('wrong_format_1'))
                        except (MessageToDeleteNotFound, MessageIdentifierNotSpecified):
                            pass
                        try:
                            await msg.bot.delete_message(msg.chat.id, data.get('wrong_format_2'))
                        except (MessageToDeleteNotFound, MessageIdentifierNotSpecified):
                            pass
                        try:
                            await msg.bot.delete_message(msg.chat.id, data.get('new_data_message'))
                        except (MessageToDeleteNotFound, MessageIdentifierNotSpecified):
                            pass
                        await msg.answer("Отлично! Проверим ваши данные:"
                                         f"\n\n<b>Имя:</b> <em>{data.get('name')}</em>"
                                         f"\n<b>Адрес доставки:</b> <em>{data.get('address')}</em>"
                                         f"\n<b>Номер телефона:</b> <em>{msg.text}</em>"
                                         f"\n\nДанные верны?",
                                         reply_markup=await inline.confirm_individual_registration())
                        await state.set_state(RegistrationUser.confirm.state)
                    else:
                        await msg.delete()
                        wrong_format = await msg.answer(
                            "❌ Количество цифр в телефоне не может быть меньше 11, попробуйте еще раз!")
                        data['wrong_format_1'] = wrong_format.message_id
                else:
                    await msg.delete()
                    wrong_format = await msg.answer(
                        "❌ Формат номера телефона должен быть +79180000000 или 89180000000, попробуйте еще раз!")
                    data['wrong_format_2'] = wrong_format.message_id
            elif msg.contact:
                await state.update_data({'phone': msg.contact.phone_number})
                try:
                    await msg.delete()
                except (MessageToDeleteNotFound, MessageIdentifierNotSpecified):
                    pass
                try:
                    await msg.bot.delete_message(msg.chat.id, data.get('phone_message'))
                except (MessageToDeleteNotFound, MessageIdentifierNotSpecified):
                    pass
                try:
                    await msg.bot.delete_message(msg.chat.id, data.get('wrong_format_1'))
                except (MessageToDeleteNotFound, MessageIdentifierNotSpecified):
                    pass
                try:
                    await msg.bot.delete_message(msg.chat.id, data.get('wrong_format_2'))
                except (MessageToDeleteNotFound, MessageIdentifierNotSpecified):
                    pass
                try:
                    await msg.bot.delete_message(msg.chat.id, data.get('new_data_message'))
                except (MessageToDeleteNotFound, MessageIdentifierNotSpecified):
                    pass
                await msg.answer("Отлично! Проверим ваши данные:"
                                 f"\n\n<b>Имя:</b> <em>{data.get('name')}</em>"
                                 f"\n<b>Адрес доставки:</b> <em>{data.get('address')}</em>"
                                 f"\n<b>Номер телефона:</b> <em>{msg.contact.phone_number}</em>"
                                 f"\n\nДанные верны?",
                                 reply_markup=await inline.confirm_individual_registration())
                await state.set_state(RegistrationUser.confirm.state)
        if data.get('update') == "Имя":
            pattern = r'^[А-ЯЁ][а-яё]+\s[А-ЯЁ][а-яё]+$'
            if not re.match(pattern, msg.text):
                await msg.delete()
                alarm_message = await msg.answer(
                    "❌ Пожалуйста, введите своё имя в формате Имя Фамилия на <b>русском языке</b>")
                data['alarm_message'] = alarm_message.message_id
            else:
                await state.update_data({"name": msg.text})
                await state.set_state(RegistrationUser.confirm.state)
                await msg.delete()
                try:
                    await msg.bot.delete_message(msg.chat.id, data.get('new_data_message'))
                except (MessageToDeleteNotFound, MessageIdentifierNotSpecified):
                    pass
                await msg.answer("Отлично! Проверим ваши данные еще раз:"
                                 f"\n\n<b>Имя:</b> <em>{msg.text}</em>"
                                 f"\n<b>Адрес доставки:</b> <em>{data.get('address')}</em>"
                                 f"\n<b>Номер телефона:</b> <em>{data.get('phone')}</em>"
                                 f"\n\nДанные верны?",
                                 reply_markup=await inline.confirm_individual_registration())
        if data.get('update') == "Адрес":
            await state.update_data({"address": msg.text})
            await state.set_state(RegistrationUser.confirm.state)
            await msg.delete()
            try:
                await msg.bot.delete_message(msg.chat.id, data.get('new_data_message'))
            except (MessageToDeleteNotFound, MessageIdentifierNotSpecified):
                pass
            await msg.answer("Отлично! Проверим ваши данные еще раз:"
                             f"\n\n<b>Имя:</b> <em>{data.get('name')}</em>"
                             f"\n<b>Адрес доставки:</b> <em>{msg.text}</em>"
                             f"\n<b>Номер телефона:</b> <em>{data.get('phone')}</em>"
                             f"\n\nДанные верны?",
                             reply_markup=await inline.confirm_individual_registration())


def register(dp: Dispatcher):
    dp.register_callback_query_handler(registration_individual_start, text='Самостоятельно')
    dp.register_message_handler(handle_individual_name, state=RegistrationUser.name)
    dp.register_message_handler(handle_individual_address, state=RegistrationUser.address)
    dp.register_message_handler(handle_individual_phone, content_types=['text', 'contact'],
                                state=RegistrationUser.phone)
    dp.register_callback_query_handler(handle_individual_confirm, state=RegistrationUser.confirm)
    dp.register_message_handler(handle_individual_update, content_types=['text', 'contact'],
                                state=RegistrationUser.update)
