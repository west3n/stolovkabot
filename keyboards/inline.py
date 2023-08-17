import datetime
import re

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import db_order_complex, db_basket


async def first_choice() -> InlineKeyboardMarkup:
    individual, corporate_entity, has_key = "Зарегистрироваться как физ.лицо", "Зарегистрировать компанию", \
        "Хочу войти по уникальному коду"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(f"🧑 {individual}", callback_data=individual)],
        [InlineKeyboardButton(f"👪 {corporate_entity}", callback_data=corporate_entity)],
        [InlineKeyboardButton(f"🔑 {has_key}", callback_data=has_key)]
    ])
    return kb


async def confirm_individual_registration():
    yes, no = "Да", "Нет"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(f"🟩 {yes}", callback_data=yes),
         InlineKeyboardButton(f"🟥 {no}", callback_data=no)],
    ])
    return kb


async def change_individual_data_reg() -> InlineKeyboardMarkup:
    name, address, phone, back = "Имя", "Адрес", "Номер", "Назад"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(f"🧑 {name}", callback_data=name),
         InlineKeyboardButton(f"🏢 {address}", callback_data=address),
         InlineKeyboardButton(f"📞 {phone}", callback_data=phone)],
        [InlineKeyboardButton(f"↩️ {back}", callback_data=back)]
    ])
    return kb


async def change_company_data_reg() -> InlineKeyboardMarkup:
    name, address, next_step = "Изменить имя компании", "Изменить адрес компании", "Всё верно, продолжаем регистрацию",
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(f"🧑 {name}", callback_data=name)],
        [InlineKeyboardButton(f"🏢 {address}", callback_data=address)],
        [InlineKeyboardButton(f"✅ {next_step}", callback_data=next_step)]
    ])
    return kb


async def change_user_data_reg() -> InlineKeyboardMarkup:
    name, phone, back = "Имя", "Номер", "Назад"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(f"🧑 {name}", callback_data=name),
         InlineKeyboardButton(f"📞 {phone}", callback_data=phone)],
        [InlineKeyboardButton(f"↩️ {back}", callback_data=back)]
    ])
    return kb


async def main_menu(tg_id) -> InlineKeyboardMarkup:
    basket_sum = await db_basket.get_basket_sum(tg_id)
    complex_lunch, assembly_lunch, profile = "Заказать комплексный обед", "Соcтавить обед самостоятельно", "Мой профиль"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(f"🍱 {complex_lunch}", callback_data=complex_lunch)],
        [InlineKeyboardButton(f"🥘 {assembly_lunch}", callback_data=f"{assembly_lunch}/salad")],
        [InlineKeyboardButton(f"️🪪 {profile}", callback_data=profile)]
    ])
    if basket_sum > 0:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(f"🍱 {complex_lunch}", callback_data=complex_lunch)],
            [InlineKeyboardButton(f"🥘 {assembly_lunch}", callback_data=f"{assembly_lunch}/salad")],
            [InlineKeyboardButton(f"️🪪 {profile}", callback_data=profile)],
            [InlineKeyboardButton(f"🧺 Моя корзина ({basket_sum} ₽)", callback_data="Моя корзина")]
        ])
    return kb


async def profile_menu(company) -> InlineKeyboardMarkup:
    if company is not None:
        order, phone, back = "Мои заказы", "Изменить номер телефона", "Главное меню"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(f"🍽 {order}", callback_data=order)],
            [InlineKeyboardButton(f"📞 {phone}", callback_data=phone)],
            [InlineKeyboardButton(f"↩️ {back}", callback_data=back)]
        ])
    else:
        order, phone, address, back = "Мои заказы", "Изменить номер телефона", "Изменить адрес доставки", "Главное меню"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(f"🍽 {order}", callback_data=order)],
            [InlineKeyboardButton(f"📞 {phone}", callback_data=phone)],
            [InlineKeyboardButton(f"📍 {address}", callback_data=address)],
            [InlineKeyboardButton(f"↩️ {back}", callback_data=back)]
        ])
    return kb


async def order_complex_choice() -> InlineKeyboardMarkup:
    today, many_days, back = "Заказать на сегодня", "Заказать на несколько дней", "Назад"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(f"🍽 {today}", callback_data=today)],
        [InlineKeyboardButton(f"📅 {many_days}", callback_data=many_days)],
        [InlineKeyboardButton(f"️↩️ {back}", callback_data='back_order_complex')]
    ])
    return kb


async def one_day_complex_paginate(weekday, tg_id, results, current_index) -> InlineKeyboardMarkup:
    basket_sum = await db_basket.get_basket_sum(tg_id)
    markup = InlineKeyboardMarkup()
    if current_index == 0:
        markup.row(InlineKeyboardButton("След.ланч ▶️", callback_data=f"next:{current_index}"))
    elif current_index == len(results) - 1:
        markup.row(InlineKeyboardButton("◀️ Пред. ланч", callback_data=f"prev:{current_index}"))
    else:
        markup.row(
            InlineKeyboardButton("◀️ Пред.ланч", callback_data=f"prev:{current_index}"),
            InlineKeyboardButton("След.ланч ▶️", callback_data=f"next:{current_index}")
        )
    markup.row(InlineKeyboardButton('🍴 Добавить в заказ', callback_data=f'order_{current_index}'))
    if basket_sum > 0:
        markup.row(InlineKeyboardButton(f"🧺 Моя корзина ({basket_sum} ₽)", callback_data="Моя корзина"))
    if weekday:
        markup.row(InlineKeyboardButton(f"📅 Выбрать другой день", callback_data="Заказать на несколько дней"))
    markup.row(InlineKeyboardButton('🔽 Главное меню', callback_data='main_menu_complex'))
    markup.add()
    return markup


async def order_complex_choice_price(lunch_id) -> InlineKeyboardMarkup:
    full_price, price_wo_salad, price_wo_soup = await db_order_complex.get_lunch_price(lunch_id)
    full, wo_salat, wo_soup, back = f"Добавить в корзину - {full_price} ₽", \
        f"Добавить в корзину без салата - {price_wo_salad} ₽", \
        f"Добавить в корзину без супа - {price_wo_soup} ₽", "Назад"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(f"️🌟 {full}", callback_data="full_price")],
        [InlineKeyboardButton(f"🚫 {wo_salat}", callback_data="wo_salat")],
        [InlineKeyboardButton(f"🚫 {wo_soup}", callback_data="wo_soup")],
        [InlineKeyboardButton(f"↩️ {back}", callback_data="back_price")]

    ])
    return kb


async def complex_count(count) -> InlineKeyboardMarkup:
    button1, prev_, next_, done, back = "Выберите количество:", "◀️", "▶️", "Подтвердить", "Назад"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(f"️{button1}", callback_data="blablabla")],
        [InlineKeyboardButton(f"{prev_}", callback_data=f"prevcount:{count}"),
         InlineKeyboardButton(f"{count}", callback_data=count),
         InlineKeyboardButton(f"{next_}", callback_data=f"nextcount:{count}")],
        [InlineKeyboardButton(f"{done}", callback_data=f"donecount:{count}")],
        [InlineKeyboardButton(f"↩️ {back}", callback_data="backcount")]
    ])
    return kb


async def order_custom_paginate(tg_id, dish_type, current_index, results) -> InlineKeyboardMarkup:
    basket_sum = await db_basket.get_basket_sum(tg_id)
    transitions = {
        'salad': ('soup', '🍲 Перейти к выбору супа'),
        'soup': ('maindish', '🍱 Перейти к выбору основного блюда'),
        'maindish': ('garnish', '🍚 Перейти к выбору гарнира'),
        'garnish': ('finish', '🏆 Закончить выбор')
    }
    prev_steps = {
        'soup': ('salad', '🥗 Вернуться к выбору салата'),
        'maindish': ('soup', '🍲 Вернуться к выбору супа'),
        'garnish': ('maindish', '🍱 Вернуться к выбору основного блюда'),
    }
    markup = InlineKeyboardMarkup()
    prev_button = InlineKeyboardButton("◀️ Пред.блюдо", callback_data=f"prev:{current_index}")
    next_button = InlineKeyboardButton("След.блюдо ▶️", callback_data=f"next:{current_index}")
    add_to_order_button = InlineKeyboardButton('🍴 Добавить в заказ', callback_data=f'order_{current_index}')
    main_menu_button = InlineKeyboardButton(
        transitions[dish_type][1], callback_data=f"Соcтавить обед самостоятельно/{transitions[dish_type][0]}")
    if current_index == 0:
        markup.row(next_button)
        markup.row(add_to_order_button)
    elif current_index == len(results) - 1:
        markup.row(prev_button)
        markup.row(add_to_order_button)
    else:
        markup.row(prev_button, next_button)
        markup.row(add_to_order_button)
    if dish_type != 'salad':
        prev_step_button = InlineKeyboardButton(
            prev_steps[dish_type][1], callback_data=f"Соcтавить обед самостоятельно/{prev_steps[dish_type][0]}")
        markup.row(prev_step_button)
    markup.row(main_menu_button)
    markup.row(InlineKeyboardButton('◀️ Главное меню', callback_data='main_menu_custom'))
    if basket_sum > 0:
        markup.row(InlineKeyboardButton(f"🧺 Моя корзина ({basket_sum} ₽)", callback_data="Моя корзина"))
    return markup


async def weekdays() -> InlineKeyboardMarkup:
    back = "Назад"
    current_date = datetime.datetime.now().date()
    days_of_week_ru_full = {
        'mon': 'Понедельник',
        'tue': 'Вторник',
        'wed': 'Среда',
        'thu': 'Четверг',
        'fri': 'Пятница',
        'sat': 'Суббота',
        'sun': 'Воскресенье'
    }
    days_of_week = []
    for i in range(7):
        day = current_date + datetime.timedelta(days=i)
        day_of_week = day.strftime('%a').lower()
        days_of_week.append([InlineKeyboardButton(f"📅 {days_of_week_ru_full[day_of_week]} "
                                                  f"({day.strftime('%d.%m')})", callback_data=day_of_week)])
    kb = InlineKeyboardMarkup(inline_keyboard=[
        *days_of_week,
        [InlineKeyboardButton(f"️↩️ {back}", callback_data='back_order_complex')]
    ])
    return kb


async def basket_menu() -> InlineKeyboardMarkup:
    change_data, add_drink, add_bake, send_to_delivery, back = "Изменить данные", "Добавить напиток", \
        "Добавить выпечку", "Отправить заказ", "Назад"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(f"️🔀 {change_data}", callback_data='change_basket')],
        [InlineKeyboardButton(f"️🍹 {add_drink}", callback_data='add_drink')],
        [InlineKeyboardButton(f"️🥐 {add_bake}", callback_data='add_bake')],
        [InlineKeyboardButton(f"️🚚 {send_to_delivery}", callback_data='send_to_delivery')],
        [InlineKeyboardButton(f"️↩️ {back}", callback_data='back_order_complex')]
    ])
    return kb


async def drinks_menu_paginate(current_index, results, tg_id) -> InlineKeyboardMarkup:
    basket_sum = await db_basket.get_basket_sum(tg_id)
    markup = InlineKeyboardMarkup()
    prev_button = InlineKeyboardButton("◀️ Пред.напиток", callback_data=f"prev:{current_index}")
    next_button = InlineKeyboardButton("След.напиток ▶️", callback_data=f"next:{current_index}")
    if current_index == 0:
        markup.row(next_button)
    elif current_index == len(results) - 1:
        markup.row(prev_button)
    else:
        markup.row(prev_button, next_button)
    markup.row(InlineKeyboardButton('📏 Выбрать объем напитка', callback_data='drink_volume'))
    markup.row(InlineKeyboardButton(f'🧺 Вернуться в корзину ({basket_sum} ₽)', callback_data="Моя корзина (напитки)"))
    markup.row(InlineKeyboardButton('◀️ Главное меню', callback_data='main_menu_drinks'))
    return markup


async def select_weekday(weekdays_list) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    for weekday in weekdays_list:
        markup.row(InlineKeyboardButton(f'📅 {weekday}', callback_data=f'day_{weekday}'))
    markup.row(InlineKeyboardButton("📅 Добавить во все дни", callback_data=f'day_all_days'))
    markup.row(InlineKeyboardButton("◀️ Назад", callback_data=f'weekdays_back'))
    return markup


async def drink_volumes(volumes) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    buttons = []
    for volume in volumes:
        buttons.append(InlineKeyboardButton(f'{volume[0]}', callback_data=f'volume_{volume[0].replace("л.", "")}'))
    markup.add(*buttons)
    markup.row(InlineKeyboardButton("◀️ Назад", callback_data=f'volume_back'))
    return markup


async def select_weekday_bakery(weekdays_list) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    for weekday in weekdays_list:
        markup.row(InlineKeyboardButton(f'📅 {weekday}', callback_data=f'day_{weekday}'))
    markup.row(InlineKeyboardButton("◀️ Назад", callback_data=f'weekdays_back'))
    return markup


async def bakery_menu_paginate(current_index, results, tg_id) -> InlineKeyboardMarkup:
    basket_sum = await db_basket.get_basket_sum(tg_id)
    markup = InlineKeyboardMarkup()
    prev_button = InlineKeyboardButton("◀️ Пред.выпечка", callback_data=f"prev:{current_index}")
    next_button = InlineKeyboardButton("След.выпечка ▶️", callback_data=f"next:{current_index}")
    if current_index == 0:
        markup.row(next_button)
    elif current_index == len(results) - 1:
        markup.row(prev_button)
    else:
        markup.row(prev_button, next_button)
    markup.row(InlineKeyboardButton('🍴 Добавить в заказ', callback_data=f'order_{current_index}'))
    markup.row(InlineKeyboardButton(f'🧺 Вернуться в корзину ({basket_sum} ₽)', callback_data="Моя корзина (выпечка)"))
    markup.row(InlineKeyboardButton('◀️ Главное меню', callback_data='main_menu_bakery'))
    return markup


async def select_weekday_basket(weekdays_list):
    markup = InlineKeyboardMarkup()
    for weekday in weekdays_list:
        markup.row(InlineKeyboardButton(f'📅 {weekday}', callback_data=f'day_{weekday}'))
    markup.row(InlineKeyboardButton("◀️ Назад", callback_data=f'Моя корзина'))
    return markup


async def change_basket_kb(weekday, tg_id):
    markup = InlineKeyboardMarkup()
    basket = await db_basket.get_basket_by_day(weekday, tg_id)
    dishes = basket[3].split('\n')
    x = 0
    for dish in dishes:
        dish_count = dish.split(" : ")[1]
        markup.row(InlineKeyboardButton(dish, callback_data=f"{x}_{dish_count}_change"))
        x += 1
    markup.row(InlineKeyboardButton(f'❌ Удалить все пункты', callback_data=f'del_{weekday}'))
    markup.row(InlineKeyboardButton("◀️ Назад", callback_data=f'change_basket'))
    return markup


async def change_dish_kb(count):
    try:
        count = count.split(" ")[0]
    except AttributeError:
        count = count
    markup = InlineKeyboardMarkup()
    small = InlineKeyboardButton(f"◀️", callback_data=f"prevcount:{count}")
    count_button = InlineKeyboardButton(f"{count}", callback_data=count)
    big = InlineKeyboardButton(f"▶️", callback_data=f"nextcount:{count}")
    delete = InlineKeyboardButton(f"❌", callback_data=f"deletecount")
    markup.row(small, count_button, big, delete)
    markup.row(InlineKeyboardButton(f"Подтвердить", callback_data=f'donecount:{count}'))
    markup.row(InlineKeyboardButton(f'↩️ Назад', callback_data='backcount'))
    return markup


async def orders_paginate(results, current_index) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    if current_index == 0:
        markup.row(InlineKeyboardButton("След.заказ ▶️", callback_data=f"next:{current_index}"))
    elif current_index == len(results) - 1:
        markup.row(InlineKeyboardButton("◀️ Пред. заказ", callback_data=f"prev:{current_index}"))
    else:
        markup.row(
            InlineKeyboardButton("◀️ Пред.заказ", callback_data=f"prev:{current_index}"),
            InlineKeyboardButton("След.заказ ▶️", callback_data=f"next:{current_index}")
        )
    markup.row(InlineKeyboardButton('🔽 Вернуться в профиль', callback_data='Мой профиль'))
    markup.add()
    return markup
