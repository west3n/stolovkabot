from aiogram import Dispatcher
import logging

from aiogram import types
from decouple import config
from handlers.commands import register as reg_handlers
from handlers.registration.individuals import register as reg_registration_individuals
from handlers.registration.company import register as reg_registration_company

bot_token = config("BOT_TOKEN")
logger = logging.getLogger(__name__)


async def set_default_commands(dp):
    await dp.bot.set_my_commands([
        types.BotCommand("start", "Начало работы с ботом")
    ])


def register_handlers(dp: Dispatcher):
    reg_handlers(dp)
    reg_registration_individuals(dp)
    reg_registration_company(dp)
