import datetime

import decouple
from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.utils.exceptions import MessageToDeleteNotFound, MessageIdentifierNotSpecified, MessageNotModified

import handlers.main_menu
from configuration import settings
from database import db_basket, db_customer, db_orders, db_company
from keyboards import inline

weekdays = {
    "Понедельник": "mon",
    "Вторник": "tue",
    "Среда": "wed",
    "Четверг": "thu",
    "Пятница": "fri",
    "Суббота": "sat",
    "Воскресенье": "sun"
}


class Drinks(StatesGroup):
    drink = State()


class Bakery(StatesGroup):
    bake = State()


class Changes(StatesGroup):
    change = State()


async def handle_basket(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        try:
            await call.bot.delete_message(call.from_user.id, data.get('photo'))
        except (MessageToDeleteNotFound, MessageIdentifierNotSpecified):
            pass
        try:
            for message in data.get('media_group'):
                await call.bot.delete_message(call.message.chat.id, int(message.message_id))
        except (MessageToDeleteNotFound, MessageIdentifierNotSpecified, TypeError, AttributeError):
            pass
    await state.finish()
    text = await db_basket.get_basket(call.from_user.id)
    if len(text) > 1:
        async with state.proxy() as data:
            weekday_buttons = []
            for day in text:
                weekday_buttons.append(day[0])
            data['weekday_buttons'] = weekday_buttons
    basket_sum = await db_basket.get_basket_sum(call.from_user.id)
    header = f'<b>Моя корзина:</b> <em>({basket_sum} ₽)</em>\n\n'
    formatted_text = header + '\n\n'.join([f"<b>{day}:</b>\n{meals}\n<b>Цена:</b> "
                                           f"<em>{price:.1f}₽</em>" for day, meals, price in text])
    await call.message.edit_text(formatted_text, reply_markup=await inline.basket_menu())


async def handle_drink(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(Drinks.drink.state)
    async with state.proxy() as data:
        text = await db_basket.get_basket(call.from_user.id)
        if data.get('weekday_buttons') or len(text) > 1:
            weekday_buttons = data.get('weekday_buttons')
            if not weekday_buttons:
                weekday_buttons = []
                for day in text:
                    weekday_buttons.append(day[0])
            await call.message.edit_text('Выберите день, в который хотите добавить напиток:',
                                         reply_markup=await inline.select_weekday(weekday_buttons))
        else:
            await add_drink(call, state)


async def add_drink(call: types.CallbackQuery, state: FSMContext):
    volumes = await db_basket.get_drink_volumes()
    volumes_list = [line.split(' - ') for line in volumes.split('\n')]
    async with state.proxy() as data:
        if call.data == 'Моя корзина (напитки)':
            await handle_basket(call, state)
        elif call.data == 'weekdays_back':
            await state.finish()
            await handle_basket(call, state)
        elif call.data.startswith('donecount'):
            drink_data = await db_basket.get_drink_data(data.get('drink_id'))
            drink_price = await db_basket.get_drink_price(drink_data[1], data.get('volume'))
            count = data.get('count') if data.get('count') else 1
            weekday = None if data.get('weekday') in [None, 'all'] else data.get('weekday')
            await db_basket.update_basket_drink(
                call.from_user.id, weekday,
                f"{drink_data[1]} {data.get('volume')} л. : {count} шт.", count * int(drink_price[0]))
            await call.answer(text=f"🧺 Вы добавили в корзину:"
                                   f"\n\n{drink_data[1]} {data.get('volume')}л."
                                   f"\nКоличество: {count}"
                                   f"\n\nОбщая цена: {count * int(drink_price[0])}₽",
                              show_alert=True)
            await call.message.edit_reply_markup(
                await inline.drinks_menu_paginate(data.get('current_index') if data.get('current_index') else 0,
                                                  data.get('results'), call.from_user.id))
        elif call.data == 'backcount':
            await call.message.edit_reply_markup(reply_markup=await inline.drink_volumes(volumes_list))
        elif call.data in map(str, range(1, 31)):
            await call.answer(f"Пока что вы выбрали {call.data} напитка!")
        elif call.data == 'blablabla':
            await call.answer("Выберите количество")
        elif call.data.startswith('prevcount') or call.data.startswith('nextcount'):
            callback_data_count = call.data.split(":")
            count = int(callback_data_count[1])
            action_count = callback_data_count[0]
            if action_count == "nextcount":
                if count + 1 <= 30:
                    count += 1
                else:
                    count = 1
            elif action_count == "prevcount":
                if count > 1:
                    count -= 1
                else:
                    count = 30
            data['count'] = count
            await call.message.edit_reply_markup(reply_markup=await inline.complex_count(count))
        elif call.data.startswith('volume_'):
            if call.data.split('_')[1] == 'back':
                await call.message.edit_reply_markup(
                    await inline.drinks_menu_paginate(data.get('current_index') if data.get('current_index') else 0,
                                                      data.get('results'), call.from_user.id))
            else:
                count = data.get('count') if data.get('count') else 1
                data['volume'] = call.data.split('_')[1]
                await call.message.edit_reply_markup(reply_markup=await inline.complex_count(count))
        elif call.data == 'drink_volume':
            await call.message.edit_reply_markup(reply_markup=await inline.drink_volumes(volumes_list))
        else:
            await call.message.delete()
            try:
                await call.bot.delete_message(call.message.chat.id, data.get('cap'))
            except (MessageToDeleteNotFound, MessageIdentifierNotSpecified, TypeError, AttributeError):
                pass
            try:
                await call.bot.delete_message(call.message.chat.id, data.get('photo'))
            except (MessageToDeleteNotFound, MessageIdentifierNotSpecified, TypeError, AttributeError):
                pass
            if call.data.startswith('day_'):
                data['weekday'] = call.data.split('_')[1]
            if call.data == 'main_menu_drinks':
                await state.finish()
                await call.message.answer(
                    "Выберите один из вариантов:", reply_markup=await inline.main_menu(call.from_user.id))
            else:
                results = await db_basket.get_drinks()
                current_index = 0
                if call.data.startswith('prev') or call.data.startswith('next'):
                    callback_data = call.data.split(":")
                    current_index = int(callback_data[1])
                    action = callback_data[0]
                    if action == "next":
                        if current_index + 1 < len(results):
                            current_index += 1
                    elif action == "prev":
                        if current_index > 0:
                            current_index -= 1
                result = results[current_index]
                # [0]: ID напитка, [1]: Имя напитка, [2]: Ссылка на картинку, [3]: FileID блюда,
                # [4]: Цена, [5]: Объем
                text = f'<b>Название напитка:</b> {result[1]}\n\n<b>Варианты объема:</b>\n{volumes}'
                photo = await call.message.answer_photo(result[3])
                cap = await call.message.answer(
                    text, reply_markup=await inline.drinks_menu_paginate(current_index, results, call.from_user.id))
                data['photo'] = photo.message_id
                data['cap'] = cap.message_id
                data['current_index'] = current_index
                data['results'] = results
                data['drink_id'] = result[0]


async def handle_bakery(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(Bakery.bake.state)
    async with state.proxy() as data:
        text = await db_basket.get_basket(call.from_user.id)
        if data.get('weekday_buttons') or len(text) > 1:
            weekday_buttons = data.get('weekday_buttons')
            if not weekday_buttons:
                weekday_buttons = []
                for day in text:
                    weekday_buttons.append(day[0])
            await call.message.edit_text('Выберите день, в который хотите добавить напиток:',
                                         reply_markup=await inline.select_weekday_bakery(weekday_buttons))
        else:
            await add_bake(call, state)


async def add_bake(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        if call.data == 'Моя корзина (выпечка)':
            await handle_basket(call, state)
        elif call.data.startswith('order_'):
            count = data.get('count') if data.get('count') else 1
            await call.message.edit_reply_markup(reply_markup=await inline.complex_count(count))
        elif call.data == 'main_menu_bakery':
            try:
                await call.message.delete()
            except MessageToDeleteNotFound:
                pass
            try:
                await call.bot.delete_message(call.from_user.id, data.get('cap'))
            except (MessageToDeleteNotFound, MessageIdentifierNotSpecified):
                pass
            try:
                await call.bot.delete_message(call.from_user.id, data.get("photo"))
            except (MessageToDeleteNotFound, MessageIdentifierNotSpecified):
                pass
            await state.finish()
            await call.message.answer(
                "Выберите один из вариантов:", reply_markup=await inline.main_menu(call.from_user.id))
        elif call.data.startswith('donecount'):
            bakery_data = await db_basket.get_bakery_data(data.get('bakery_id'))
            count = data.get('count') if data.get('count') else 1
            await db_basket.update_basket_bakery(f"{bakery_data[1]} : {count} шт.",
                                                 (count * bakery_data[9]), call.from_user.id, data.get('weekday'))
            await call.answer(text=f"🧺 Вы добавили в корзину:"
                                   f"\n\n{bakery_data[1]}"
                                   f"\nКоличество порций: {count}"
                                   f"\n\nОбщая цена: {count * bakery_data[9]}₽",
                              show_alert=True)
            await call.message.edit_reply_markup(
                reply_markup=await inline.bakery_menu_paginate(
                    data.get('current_index'), data.get('results'), call.from_user.id))
        elif call.data == 'backcount':
            await call.message.edit_reply_markup(
                reply_markup=await inline.bakery_menu_paginate(
                    data.get('current_index'), data.get('results'), call.from_user.id))
        elif call.data in map(str, range(1, 31)):
            await call.answer(f"Пока что вы выбрали {call.data} порций!")
        elif call.data == 'blablabla':
            await call.answer("Выберите количество")
        elif call.data.startswith('prevcount') or call.data.startswith('nextcount'):
            callback_data_count = call.data.split(":")
            count = int(callback_data_count[1])
            action_count = callback_data_count[0]
            if action_count == "nextcount":
                if count + 1 <= 30:
                    count += 1
                else:
                    count = 1
            elif action_count == "prevcount":
                if count > 1:
                    count -= 1
                else:
                    count = 30
            data['count'] = count
            await call.message.edit_reply_markup(reply_markup=await inline.complex_count(count))
        else:
            if call.data.startswith('day'):
                data['weekday'] = call.data.split('_')[1]
            else:
                text = await db_basket.get_basket(call.from_user.id)
                data['weekday'] = text[0][0]
            try:
                await call.message.delete()
            except MessageToDeleteNotFound:
                pass
            try:
                await call.bot.delete_message(call.message.chat.id, data.get('cap'))
            except (MessageToDeleteNotFound, MessageIdentifierNotSpecified, TypeError, AttributeError):
                pass
            try:
                await call.bot.delete_message(call.message.chat.id, data.get('photo'))
            except (MessageToDeleteNotFound, MessageIdentifierNotSpecified, TypeError, AttributeError):
                pass
            weekday = data.get('weekday').split(" ")[0]
            weekday_dict = weekdays[weekday]
            results = await db_basket.get_weekday_bake(weekday_dict)
            current_index = 0
            if call.data.startswith('prev') or call.data.startswith('next'):
                callback_data = call.data.split(":")
                current_index = int(callback_data[1])
                action = callback_data[0]
                if action == "next":
                    if current_index + 1 < len(results):
                        current_index += 1
                elif action == "prev":
                    if current_index > 0:
                        current_index -= 1
            result = results[current_index]
            text = f'<b>Название выпечки:</b> {result[1]}' \
                   f'\n\n<b>Цена:</b> {int(result[9])} ₽'
            photo = await call.message.answer_photo(result[3])
            cap = await call.message.answer(
                text, reply_markup=await inline.bakery_menu_paginate(current_index, results, call.from_user.id))
            # [0]: ID блюда, [1]: Имя блюда, [2]: Ссылка на картинку, [3]: FileID блюда,
            # [4]: Калории, [5]: Белки, [6]: Жиры, [7]: Углеводы, [8]: Состав, [9]: Цена, [10]: День недели
            data['photo'] = photo.message_id
            data['cap'] = cap.message_id
            data['current_index'] = current_index
            data['results'] = results
            data['bakery_id'] = result[0]


async def send_to_delivery(call: types.CallbackQuery):
    message = await call.message.edit_text('Заказ отправляется, ожидайте...')
    await call.bot.send_chat_action(call.message.chat.id, 'typing')
    user_data = await db_customer.get_customer(call.from_user.id)
    company_name = await db_company.get_company_data(user_data[3]) if user_data[3] else None
    user_data = [user_data[1], user_data[2], company_name[1] if company_name else "Нет компании", user_data[4]]
    order_data = await db_basket.get_full_basket(call.from_user.id)
    now = datetime.datetime.now().strftime('%d.%m.%Y %H:%M')
    sh = await settings.sheets_connection()
    worksheet_name = "TEST"
    worksheet = sh.worksheet(worksheet_name)
    for data in order_data:
        full_data = [now] + list(user_data) + data
        worksheet.append_row(full_data, 2)
    await db_orders.add_new_order(call.from_user.id)
    await db_basket.delete_basket(call.from_user.id)
    await call.bot.delete_message(call.message.chat.id, message.message_id)
    await call.answer('😊 Спасибо что выбрали нас!\n'
                      '🎊 Заказ успешно отправлен! Ожидайте подтверждения от администратора! \n\n'
                      'Вы можете посмотреть заказ в разделе "Мои профиль" -> "Мои заказы"',
                      show_alert=True)
    formatted_text = '\n\n'.join([f"<b>{day}:</b>\n{meals}\n<b>Цена:</b>"
                                  f"<em> {price:.1f}₽</em>" for day, meals, price in order_data])
    await call.bot.send_message(
        decouple.config("GROUP_ID"),
        f"<b>Пользователь {'@' + call.from_user.username if call.from_user.username else user_data[2]} создал заказ!</b>"
        f"\n\n<em>Компания: {user_data[2]}</em>"
        f"\n\n<b>Заказ:</b>\n{formatted_text}"
        f"\n\n<b>Адрес доставки</b>: {user_data[3]}")
    await call.message.answer("Выберите один из вариантов:", reply_markup=await inline.main_menu(call.from_user.id))


async def change_basket(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        await state.set_state(Changes.change.state)
        basket = await db_basket.get_basket(call.from_user.id)
        if call.data.startswith('donecount:'):
            await db_basket.change_dish_in_basket(
                call.from_user.id, data.get('weekday'), call.data.split(":")[1], data.get('dish'))
            await call.answer(f"Количество {data.get('dish').split(':')[0]} успешно обновлено!",
                              show_alert=True)
            await call.message.edit_text(
                f"Вы выбрали {data.get('weekday')}\nВыберите пункт, который хотите изменить:",
                reply_markup=await inline.change_basket_kb(data.get('weekday'), call.from_user.id))
        elif call.data == 'deletecount':
            await db_basket.delete_dish_from_basket(data.get('dish'), data.get('weekday'), call.from_user.id)
            basket = await db_basket.get_basket_by_day(data.get('weekday'), call.from_user.id)
            await call.answer(f"{data.get('dish')} удалено из корзины!",
                              show_alert=True)
            if basket:
                await call.message.edit_text(
                    f"Вы выбрали {data.get('weekday')}\nВыберите пункт, который хотите изменить:",
                    reply_markup=await inline.change_basket_kb(data.get('weekday'), call.from_user.id))
            else:
                await state.finish()
                await handlers.main_menu.main_menu_call(call)
        elif call.data == 'backcount':
            weekday = data.get('weekday')
            await call.message.edit_text(
                f"Вы выбрали {weekday}\nВыберите пункт, который хотите изменить:",
                reply_markup=await inline.change_basket_kb(weekday, call.from_user.id))
        elif call.data.startswith('prevcount') or call.data.startswith('nextcount'):
            callback_data_count = call.data.split(":")
            count = int(callback_data_count[1])
            action_count = callback_data_count[0]
            if action_count == "nextcount":
                if count + 1 <= 30:
                    count += 1
                else:
                    count = 1
            elif action_count == "prevcount":
                if count > 1:
                    count -= 1
                else:
                    count = 30
            data['count'] = count
            await call.message.edit_reply_markup(reply_markup=await inline.change_dish_kb(count))
        elif call.data.endswith('_change'):
            dish_index = call.data.split('_')[0]
            amount = call.data.split('_')[1]
            basket = await db_basket.get_basket_by_day(data.get('weekday'), call.from_user.id)
            dish = basket[3].split('\n')[int(dish_index)].split(':')[0]
            data['dish'] = basket[3].split('\n')[int(dish_index)]
            data['amount'] = amount
            await call.message.edit_text(f"Выберите новое количество или удалите <b>{dish}:</b>",
                                         reply_markup=await inline.change_dish_kb(amount))
        elif call.data.startswith('day_'):
            weekday = call.data.split('_')[1]
            data['weekday'] = weekday
            await call.message.edit_text(
                f"Вы выбрали {weekday}\nВыберите пункт, который хотите изменить:",
                reply_markup=await inline.change_basket_kb(weekday, call.from_user.id))
        elif call.data.startswith('del_'):
            weekday = call.data.split('_')[1]
            await db_basket.delete_basket_by_day(weekday, call.from_user.id)
            basket = await db_basket.get_basket(call.from_user.id)
            await state.finish()
            if basket:
                await handle_basket(call, state)
            else:
                await state.finish()
                await handlers.main_menu.main_menu_call(call)
        else:
            if len(basket) > 1:
                weekday_buttons = []
                for day in basket:
                    weekday_buttons.append(day[0])
                await call.message.edit_text(
                    "Выберите день, в котором хотите изменить данные:",
                    reply_markup=await inline.select_weekday_basket(weekday_buttons))
            else:
                try:
                    weekday = basket[0][0]
                    data['weekday'] = weekday
                    await call.message.edit_text(
                        f"Вы выбрали {weekday}\nВыберите пункт, который хотите изменить:",
                        reply_markup=await inline.change_basket_kb(weekday, call.from_user.id))
                except MessageNotModified:
                    await handle_basket(call, state)


def register(dp: Dispatcher):
    dp.register_callback_query_handler(handle_basket, text='Моя корзина', state='*')
    dp.register_callback_query_handler(handle_drink, text='add_drink', state='*')
    dp.register_callback_query_handler(add_drink, state=Drinks.drink)
    dp.register_callback_query_handler(handle_bakery, text='add_bake', state='*')
    dp.register_callback_query_handler(add_bake, state=Bakery.bake)
    dp.register_callback_query_handler(send_to_delivery, text='send_to_delivery')
    dp.register_callback_query_handler(change_basket, text='change_basket')
    dp.register_callback_query_handler(change_basket, state=Changes.change)
