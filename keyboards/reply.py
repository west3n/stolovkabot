from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton

kb_remove = ReplyKeyboardRemove()


async def contact() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton('Отправить контакт', request_contact=True)]
    ], resize_keyboard=True, one_time_keyboard=True)
    return kb

