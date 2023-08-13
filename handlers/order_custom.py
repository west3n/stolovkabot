import datetime
import psycopg2

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.utils.exceptions import MessageToDeleteNotFound, MessageIdentifierNotSpecified

from database import db_order_custom, db_basket
from keyboards import inline


class OrderCustom(StatesGroup):
    salad = State()
    soup = State()
    main_dish = State()
    garnish = State()


weekdays = {
    0: "mon",
    1: "tue",
    2: "wed",
    3: "thu",
    4: "fri",
    5: "sat",
    6: "sun"
}


async def custom_order_handler_paginate(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(OrderCustom.salad.state)
    async with state.proxy() as data:
        weekday = datetime.datetime.now().weekday()
        weekday = weekdays.get(weekday)
        dish_type = data.get('dish_type')
        if call.data.startswith('order_'):
            count = data.get('count') if data.get('count') else 1
            await call.message.edit_reply_markup(reply_markup=await inline.complex_count(count))
        elif call.data == 'main_menu_custom':
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
            dish_data = await db_order_custom.get_dish_info(data.get('dish_type'), data.get('dish_id'))
            count = data.get('count') if data.get('count') else 1
            await db_basket.insert_basket(weekday, call.from_user.id, f"{dish_data[1]} - {data.get('count')} шт.",
                                          (count * dish_data[9]))
            await call.answer(text=f"🧺 Вы добавили в корзину:"
                                   f"\n\n{dish_data[1]}"
                                   f"\nКоличество порций: {data.get('count')}"
                                   f"\n\nОбщая цена: {count * dish_data[9]}₽",
                              show_alert=True)
            await call.message.edit_reply_markup(
                reply_markup=await inline.order_custom_paginate(
                    call.from_user.id, dish_type, data.get('current_index'), data.get('results')))
        elif call.data == 'backcount':
            await call.message.edit_reply_markup(
                reply_markup=await inline.order_custom_paginate(
                    call.from_user.id, dish_type, data.get('current_index'), data.get('results')))
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
            if call.data.startswith("Соcтавить обед самостоятельно"):
                dish_type = call.data.split("/")[1]
                if dish_type == 'finish':
                    await state.finish()
                    await call.message.answer(
                        "Выберите один из вариантов:", reply_markup=await inline.main_menu(call.from_user.id))
            try:
                results = await db_order_custom.get_dish_by_day(dish_type, weekday)
            except psycopg2.Error:
                results = None
            if results:
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
                # [0]: ID блюда, [1]: Имя блюда, [2]: Ссылка на картинку, [3]: FileID блюда,
                # [4]: Калории, [5]: Белки, [6]: Жиры, [7]: Углеводы, [8]: Состав, [9]: Цена
                text = f"⭐ <b>Название блюда: {result[1]}</b>"
                text += f'\n\n<b>Калории:</b> <em>{result[4]} ккал</em>' \
                        f'\n<b>Белки:</b> <em>{result[5]} г</em>' \
                        f'\n<b>Жиры:</b> <em>{result[6]} г</em>' \
                        f'\n<b>Углеводы:</b> <em>{result[7]} г</em>'
                photo = await call.message.bot.send_photo(call.from_user.id, result[3])
                cap = await call.message.answer(
                    text, reply_markup=await inline.order_custom_paginate(
                        call.from_user.id, dish_type, current_index, results))
                data['photo'] = photo.message_id
                data['dish_type'] = dish_type
                data['cap'] = cap.message_id
                data['dish_id'] = result[0]
                data['current_index'] = current_index
                data['results'] = results


def register(dp: Dispatcher):
    dp.register_callback_query_handler(
        custom_order_handler_paginate, lambda c: c.data.startswith("Соcтавить обед самостоятельно"))
    dp.register_callback_query_handler(custom_order_handler_paginate, state=OrderCustom.salad)
