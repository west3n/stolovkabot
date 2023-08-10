from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import db_order_complex


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


async def main_menu() -> InlineKeyboardMarkup:
    complex_lunch, assembly_lunch, profile = "Заказать комплексный обед", "Соcтавить обед самостоятельно", "Мой профиль"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(f"🍱 {complex_lunch}", callback_data=complex_lunch)],
        [InlineKeyboardButton(f"🥘 {assembly_lunch}", callback_data=assembly_lunch)],
        [InlineKeyboardButton(f"️🪪 {profile}", callback_data=profile)]
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


async def one_day_complex_paginate(results, current_index) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    if current_index == 0:
        markup.row(
            InlineKeyboardButton('◀️ Главное меню', callback_data='main_menu_complex'),
            InlineKeyboardButton("След.ланч ▶️", callback_data=f"next:{current_index}"),
        )
        markup.row(InlineKeyboardButton('🍴 Добавить в заказ', callback_data=f'order_{current_index}'))
    elif current_index == len(results) - 1:
        markup.row(
            InlineKeyboardButton("◀️ Пред. ланч", callback_data=f"prev:{current_index}"),
            InlineKeyboardButton('🔽 Главное меню', callback_data='main_menu_complex'),
        )
        markup.row(InlineKeyboardButton('🍴 Добавить в заказ', callback_data=f'order_{current_index}'))
    else:
        markup.row(
            InlineKeyboardButton("◀️ Пред.ланч", callback_data=f"prev:{current_index}"),
            InlineKeyboardButton("След.ланч ▶️", callback_data=f"next:{current_index}")
        )
        markup.row(InlineKeyboardButton('🍴 Добавить в заказ', callback_data=f'order_{current_index}'))
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
