import re
import string
import random

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.utils.exceptions import MessageToDeleteNotFound, MessageIdentifierNotSpecified

from database import db_company, db_customer
from keyboards import inline, reply


class RegistrationCompany(StatesGroup):
    args = State()
    name = State()
    address = State()
    finish_company = State()
    update = State()
    user_name = State()
    user_phone = State()
    user_confirm = State()
    user_update = State()


def generate_key():
    characters = string.ascii_letters + string.digits
    key = ''.join(random.choice(characters) for _ in range(6))
    return key


async def registration_get_company_key(call: types.CallbackQuery, state: FSMContext):
    try:
        await call.message.delete()
    except MessageToDeleteNotFound:
        pass
    reg_start = await call.message.answer('🔑 Введите ключ своей компании:')
    await RegistrationCompany.args.set()
    await state.update_data({"reg_start": reg_start.message_id})


async def handle_company_key(msg: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            await msg.delete()
    except (MessageToDeleteNotFound, MessageIdentifierNotSpecified):
        pass
    try:
        await msg.bot.delete_message(msg.from_id, data.get('reg_start'))
    except (MessageToDeleteNotFound, MessageIdentifierNotSpecified):
        pass
    try:
        await msg.bot.delete_message(msg.from_id, data.get('error_message'))
    except (MessageToDeleteNotFound, MessageIdentifierNotSpecified):
        pass
    if len(msg.text) == 6:
        if msg.text in await db_company.get_all_key_list():
            company_data = await db_company.get_company_data_by_key(msg.text)
            start_message = await msg.answer(f"Вы зашли в бота через ключ компании <b>{company_data[1]}</b>."
                                             f"\n\nДля начала регистрации, введите свои <b>Имя</b> и <b>Фамилию</b>"
                                             f"\n\nНапример, Иван Иванов")
            await RegistrationCompany.user_name.set()
            async with state.proxy() as data:
                data['start_message'] = start_message.message_id
                data['company_id'] = company_data[0]
                data['address'] = company_data[2]
                data['args'] = msg.text
        else:
            error_message = await msg.answer('Данного ключа нет в списке, попробуйте ввести другой!')
            await state.update_data({"error_message": error_message.message_id})
    else:
        error_message = await msg.answer('Длина ключа должна быть 6 символов! Попробуйте заново!')
        await state.update_data({"error_message": error_message.message_id})


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
            data['args'] = None
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
    await msg.answer(f"Адрес записан! Проверьте данные еще раз:\n\n<b>Имя компании:</b> "
                     f"{data.get('name')}\n<b>Адрес:</b> {data.get('address')}",
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
            await state.set_state(RegistrationCompany.user_name.state)
    else:
        update_message = await call.message.edit_text(f'Хорошо, вы хотите {call.data.lower()}. Введите новые данные:')
        await state.set_state(RegistrationCompany.update.state)
        async with state.proxy() as data:
            data['update'] = call.data
            data['update_message'] = update_message.message_id


async def handle_new_update_company(msg: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if data.get('update') == 'Изменить адрес компании':
            await state.update_data({"address": msg.text})
            try:
                await msg.delete()
                await msg.bot.delete_message(msg.chat.id, data.get('update_message'))
            except MessageToDeleteNotFound:
                pass
            await msg.answer(f"Новый адрес записан! Проверьте данные еще раз:\n\n<b>Имя компании:</b> "
                             f"{data.get('name')}\n<b>Адрес: {msg.text}</b>",
                             reply_markup=await inline.change_company_data_reg())
        else:
            await state.update_data({'name': msg.text})
            try:
                await msg.delete()
                await msg.bot.delete_message(msg.chat.id, data.get('update_message'))
            except MessageToDeleteNotFound:
                pass
            await msg.answer(f"Новое имя компании записано!! Проверьте данные еще раз:\n\n<b>Имя компании:</b> "
                             f"{msg.text}\n<b>Адрес:</b> {data.get('address')}",
                             reply_markup=await inline.change_company_data_reg())
        await state.set_state(RegistrationCompany.finish_company.state)


async def handle_user_name(msg: types.Message, state: FSMContext):
    pattern = r'^[А-ЯЁ][а-яё]+\s[А-ЯЁ][а-яё]+$'
    if not re.match(pattern, msg.text):
        await msg.delete()
        alarm_message = await msg.answer(
            "❌ Пожалуйста, введите своё имя в формате Имя Фамилия на <b>русском языке</b>")
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
            phone_message = await msg.answer(
                f"{data.get('name')}, я сохранил ваше имя!"
                f"\n\nТеперь введите номер телефона (в формате +79180000000 или 89180000000) или нажмите кнопку ниже:",
                reply_markup=await reply.contact())
            data['phone_message'] = phone_message.message_id
            await RegistrationCompany.next()


async def handle_user_phone(msg: types.Message, state: FSMContext):
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
                                     f"\n<b>Номер телефона:</b> <em>{data.get('phone')}</em>"
                                     f"\n\nДанные верны?",
                                     reply_markup=await inline.confirm_individual_registration())
                    await RegistrationCompany.next()
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
                         f"\n<b>Номер телефона:</b> <em>{data.get('phone')}</em>"
                         f"\n\nДанные верны?",
                         reply_markup=await inline.confirm_individual_registration())
        await RegistrationCompany.next()


async def handle_user_confirm(call: types.CallbackQuery, state: FSMContext):
    if call.data == "Назад":
        async with state.proxy() as data:
            await call.message.edit_text(
                "Проверим ваши данные еще раз:"
                f"\n\n<b>Имя:</b> <em>{data.get('name')}</em>"
                f"\n<b>Номер телефона:</b> <em>{data.get('phone')}</em>"
                f"\n\nДанные верны?",
                reply_markup=await inline.confirm_individual_registration())
    elif call.data == 'Да':
        async with state.proxy() as data:
            args = data.get('args')
            secret_key = await db_company.get_company_data(data.get('company_id'))
            if args:
                text = f'Данные успешно сохранены!' \
                       f"\n\nТеперь перейдем к составлению комплексного обеда." \
                       f"\n\nВы всегда сможете изменить номер телефона и адрес доставки в 'Профиле'"
            else:
                text = f"Данные успешно сохранены! Вам необходимо сохранить ключ, по которому будут регистрироваться " \
                       f"сотрудники вашей компании: `{secret_key[3]}` (копируется касанием)" \
                       f"\n\nТакже для более удобного входа можно входить по специальной ссылке: " \
                       f"\n\n`https://t.me/stolovka_devbot?start={secret_key[3]}` (копируется касанием)" \
                       f"\n\nТеперь перейдем к составлению комплексного обеда." \
                       "\n\nВы всегда сможете изменить номер телефона и адрес доставки в 'Профиле'"
            special_chars = ['_', '.', '*', '[', ']', '(', ')', '~', '>', '#', '+', '-', '=', '|', '{', '}', '!']
            for char in special_chars:
                escaped_char = '\\' + char
                text = text.replace(char, escaped_char)
            await call.message.edit_text(text, parse_mode=types.ParseMode.MARKDOWN_V2)
            await db_customer.insert_individual_customer(data, call.from_user.id)
        await state.finish()
    elif call.data == "Нет":
        await call.message.edit_text("Какой из параметров вы хотите изменить?",
                                     reply_markup=await inline.change_user_data_reg())
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
        await RegistrationCompany.next()


async def handle_user_update(msg: types.Message, state: FSMContext):
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
                        await state.set_state(RegistrationCompany.user_confirm.state)
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
                await state.set_state(RegistrationCompany.user_confirm.state)
        if data.get('update') == "Имя":
            pattern = r'^[А-ЯЁ][а-яё]+\s[А-ЯЁ][а-яё]+$'
            if not re.match(pattern, msg.text):
                await msg.delete()
                alarm_message = await msg.answer(
                    "❌ Пожалуйста, введите своё имя в формате Имя Фамилия на <b>русском языке</b>")
                data['alarm_message'] = alarm_message.message_id
            else:
                await state.update_data({"name": msg.text})
                await state.set_state(RegistrationCompany.user_confirm.state)
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


def register(dp: Dispatcher):
    dp.register_callback_query_handler(registration_get_company_key, text='Хочу войти по уникальному коду')
    dp.register_message_handler(handle_company_key, state=RegistrationCompany.args)
    dp.register_callback_query_handler(registration_company_start, text='Зарегистрировать компанию')
    dp.register_message_handler(handle_company_name, state=RegistrationCompany.name)
    dp.register_message_handler(handle_company_address, state=RegistrationCompany.address)
    dp.register_callback_query_handler(handle_company_update, state=RegistrationCompany.finish_company)
    dp.register_message_handler(handle_new_update_company, state=RegistrationCompany.update)
    dp.register_message_handler(handle_user_name, state=RegistrationCompany.user_name)
    dp.register_message_handler(handle_user_phone, content_types=['text', 'contact'],
                                state=RegistrationCompany.user_phone)
    dp.register_callback_query_handler(handle_user_confirm, state=RegistrationCompany.user_confirm)
    dp.register_message_handler(handle_user_update, content_types=['text', 'contact'],
                                state=RegistrationCompany.user_update)
