from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.utils.exceptions import MessageToDeleteNotFound, MessageIdentifierNotSpecified

from database import db_basket
from keyboards import inline


class Drinks(StatesGroup):
    drink = State()


async def handle_basket(call: types.CallbackQuery, state: FSMContext):
    text = await db_basket.get_basket(call.from_user.id)
    basket_sum = await db_basket.get_basket_sum(call.from_user.id)
    header = f'Моя корзина: ({basket_sum} ₽)\n\n'
    formatted_text = header + '\n\n'.join([f"{day}:\n{meals}\nЦена: {price:.1f}₽" for day, meals, price in text])
    async with state.proxy() as data:
        if not data.get('cap'):
            await call.message.edit_text(formatted_text, reply_markup=await inline.basket_menu())
        else:
            try:
                for message in data.get('media_group'):
                    await call.bot.delete_message(call.message.chat.id, int(message.message_id))
            except (MessageToDeleteNotFound, MessageIdentifierNotSpecified, TypeError, AttributeError):
                pass
            try:
                message_id = data.get('cap')
                await call.bot.delete_message(call.message.chat.id, int(message_id.message_id))
            except (MessageToDeleteNotFound, MessageIdentifierNotSpecified, TypeError, AttributeError):
                pass
            await state.finish()
            await call.message.answer(formatted_text, reply_markup=await inline.basket_menu())


async def add_drink(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        await call.message.delete()
        try:
            await call.bot.delete_message(call.message.chat.id, data.get('cap'))
        except (MessageToDeleteNotFound, MessageIdentifierNotSpecified, TypeError, AttributeError):
            pass
        try:
            await call.bot.delete_message(call.message.chat.id, data.get('photo'))
        except (MessageToDeleteNotFound, MessageIdentifierNotSpecified, TypeError, AttributeError):
            pass
        if call.data == 'main_menu_drinks':
            await state.finish()
            await call.message.answer(
                "Выберите один из вариантов:", reply_markup=await inline.main_menu(call.from_user.id))
        else:
            await state.set_state(Drinks.drink.state)
            results = await db_basket.get_drinks()
            volumes = await db_basket.get_drink_volumes()
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
            cap = await call.message.answer(text, reply_markup=await inline.drinks_menu_paginate(current_index, results))
            data['photo'] = photo.message_id
            data['cap'] = cap.message_id


def register(dp: Dispatcher):
    dp.register_callback_query_handler(handle_basket, text='Моя корзина', state='*')
    dp.register_callback_query_handler(add_drink, text='add_drink')
    dp.register_callback_query_handler(add_drink, state=Drinks.drink)
