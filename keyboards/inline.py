from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


async def first_choice() -> InlineKeyboardMarkup:
    individual, corporate_entity, has_key = "Самостоятельно", "Для компании", "Хочу войти по уникальному коду"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(f"🧑 {individual}", callback_data=individual),
         InlineKeyboardButton(f"👪 {corporate_entity}", callback_data=corporate_entity)],
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