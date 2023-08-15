import datetime

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.utils.exceptions import MessageToDeleteNotFound, MessageIdentifierNotSpecified

import handlers.basket
from database import db_order_complex, db_basket
from keyboards import inline
from handlers import main_menu

days = ['mon', 'tue', 'wed', 'tue', 'fri', 'sat', 'sun']
weekdays = {i: day for i, day in enumerate(days)}
lunches = {
    'diet': 'Диетический',
    'vegan': 'Веганский',
    'lunch1': 'Обед 1',
    'lunch2': 'Обед 2',
    'lunch3': 'Обед 3',
    'lunch4': 'Обед 4',
    'lunch5': 'Обед 5'
}


class OneDayComplex(StatesGroup):
    complex_id = State()


class ManyDayComplex(StatesGroup):
    pass


async def back_button(call: types.CallbackQuery):
    await main_menu.main_menu_call(call)


async def order_complex_handler(call: types.CallbackQuery):
    await call.message.edit_text("Выберите один из вариантов:", reply_markup=await inline.order_complex_choice())


async def handle_manydays(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        await call.message.delete()
        try:
            for message in data.get('media_group'):
                await call.bot.delete_message(call.message.chat.id, int(message.message_id))
        except (MessageToDeleteNotFound, MessageIdentifierNotSpecified, TypeError, AttributeError):
            pass
        try:
            await call.bot.delete_message(call.message.chat.id, data.get('cap'))
        except (MessageToDeleteNotFound, MessageIdentifierNotSpecified, TypeError, AttributeError):
            pass
    await state.finish()
    await call.message.answer('Выберите день:', reply_markup=await inline.weekdays())


async def one_day_complex_paginate(call: types.CallbackQuery, state: FSMContext):
    await OneDayComplex.complex_id.set()
    async with state.proxy() as data:
        if call.data.startswith("donecount"):
            lunch_name = await db_order_complex.get_lunch_name(data.get('lunch_id'))
            count = int(data.get('count')) if data.get('count') else 1
            price = float(data.get('lunch_price'))
            total_price = round((count * price), 2)
            weekday = data.get('weekday') if data.get('weekday') else weekdays.get(datetime.datetime.now().weekday())
            await db_basket.insert_basket(
                    weekday, call.from_user.id, f"{lunch_name} ({data.get('lunch_type')}) : {count} шт.", total_price)
            await call.answer(text=f"🧺 Вы добавили в корзину:"
                                   f"\n\nКомплексный обед {lunch_name} ({data.get('lunch_type')})"
                                   f"\nКоличество порций: {count}"
                                   f"\n\n Общая цена: {total_price}₽",
                              show_alert=True)
            await call.message.edit_reply_markup(
                reply_markup=await inline.one_day_complex_paginate(
                    data.get('weekday'), call.from_user.id, data.get('results'), data.get('current_index')))
        elif call.data == 'Моя корзина':
            await handlers.basket.handle_basket(call, state)
        elif call.data == 'backcount':
            await call.message.edit_reply_markup(
                reply_markup=await inline.order_complex_choice_price(data.get('lunch_id')))
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
        elif call.data in ['full_price', 'wo_salat', 'wo_soup']:
            full_price, price_wo_salad, price_wo_soup = await db_order_complex.get_lunch_price(data.get('lunch_id'))
            if call.data == 'full_price':
                data['lunch_type'] = "Полный обед"
                data['lunch_price'] = full_price
            elif call.data == 'wo_salat':
                data['lunch_type'] = 'Обед без салата'
                data['lunch_price'] = price_wo_salad
            elif call.data == 'wo_soup':
                data['lunch_type'] = 'Обед без супа'
                data['lunch_price'] = price_wo_soup
            count = data.get('count') if data.get('count') else 1
            await call.message.edit_reply_markup(reply_markup=await inline.complex_count(count))
        elif call.data == 'back_price':
            await call.message.edit_reply_markup(
                reply_markup=await inline.one_day_complex_paginate(
                    data.get('weekday'), call.from_user.id, data.get('results'), data.get('current_index')))
        elif call.data.startswith('order_'):
            await call.message.edit_reply_markup(
                reply_markup=await inline.order_complex_choice_price(data.get('lunch_id')))
        elif call.data == 'main_menu_complex':
            for message in data.get('media_group'):
                await call.bot.delete_message(call.message.chat.id, int(message.message_id))
            message_id = data.get('cap')
            await call.bot.delete_message(call.message.chat.id, int(message_id.message_id))
            await state.finish()
            await call.message.answer(
                "Выберите один из вариантов:", reply_markup=await inline.main_menu(call.from_user.id))
        else:
            try:
                await call.message.delete()
            except MessageToDeleteNotFound:
                pass
            try:
                for message in data.get('media_group'):
                    try:
                        await call.bot.delete_message(call.message.chat.id, int(message.message_id))
                    except MessageToDeleteNotFound:
                        pass
                try:
                    await call.bot.delete_message(call.message.chat.id, data.get('cap'))
                except MessageToDeleteNotFound:
                    pass
            except TypeError:
                pass
            if call.data in days:
                weekday = call.data
                data['weekday'] = call.data
            else:
                weekday = datetime.datetime.now().weekday()
                weekday = weekdays.get(weekday)
                if data.get('weekday'):
                    weekday = data.get('weekday')
            results = await db_order_complex.get_all_lunches_by_weekday(weekday)
            if results:
                current_index = 0
                result = results[current_index]
                # [0]: Имя салата, [1]: FileID салата, [2]: Состав салата, [3]: Имя супа, [4]: FileID супа,
                # [5]: Состав супа, [6]: Имя основного блюда, [7]: FileID основного блюда, [8]: Состав основного блюда,
                # [9]: Имя гарнира, [10]: FileID гарнира, [11]: Состав гарнира, [12]: Количество калорий,
                # [13]: Количество белков, [14]: Количество жиров, [15]: Количество углеводов, [16]: Название ланча,
                # [17]: ID ланча
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
                media_group = []
                file_ids = []
                for index in [1, 4, 7, 10]:
                    if result[index]:
                        file_ids.append(result[index])
                for file_id in file_ids:
                    media = types.InputMediaPhoto(media=file_id)
                    media_group.append(media)
                media_group = await call.message.answer_media_group(media_group)
                lunch_name = lunches.get(result[16])
                text = f"⭐ <b>Комплексный обед: {lunch_name}</b>" \
                       f"\n\n🥗 <b>{result[0]}</b> <em>({result[2]})</em>" \
                       f"\n\n🍜 <b>{result[3]}</b> <em>({result[5]})</em>" \
                       f"\n\n🍗 <b>{result[6]}</b> <em>({result[8]})</em>"
                text += f'\n\n🍚 <b>{result[9]}</b> <em>({result[11]})</em>' if result[9] else ''
                text += f'\n\n<b>Калории:</b> <em>{result[12]} ккал</em>' \
                        f'\n<b>Белки:</b> <em>{result[13]} г</em>' \
                        f'\n<b>Жиры:</b> <em>{result[14]} г</em>' \
                        f'\n<b>Углеводы:</b> <em>{result[15]} г</em>'
                cap = await call.message.answer(
                    text, reply_markup=await inline.one_day_complex_paginate(
                        data.get('weekday'), call.from_user.id, results, current_index))
                await OneDayComplex.complex_id.set()
                data['media_group'] = media_group
                data['cap'] = cap.message_id
                data['lunch_id'] = result[17]
                data['current_index'] = current_index
                data['results'] = results


def register(dp: Dispatcher):
    dp.register_callback_query_handler(handle_manydays, text='Заказать на несколько дней', state="*")
    dp.register_callback_query_handler(back_button, text='back_order_complex')
    dp.register_callback_query_handler(order_complex_handler, text='Заказать комплексный обед')
    dp.register_callback_query_handler(one_day_complex_paginate, lambda c: c.data in days + ['Заказать на сегодня'])
    dp.register_callback_query_handler(one_day_complex_paginate, state=OneDayComplex.complex_id)
