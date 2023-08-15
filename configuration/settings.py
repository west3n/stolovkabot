import decouple
import gspread
from aiogram import Dispatcher
import logging

from aiogram import types
from decouple import config
from oauth2client.service_account import ServiceAccountCredentials

from handlers.commands import register as reg_handlers
from handlers.registration.individuals import register as reg_registration_individuals
from handlers.registration.company import register as reg_registration_company
from handlers.profile import register as reg_profile
from handlers.order_complex import register as reg_order_complex
from handlers.order_custom import register as reg_order_custom
from handlers.basket import register as reg_basket

bot_token = config("BOT_TOKEN")
logger = logging.getLogger(__name__)


async def sheets_connection():
    sheet_url = decouple.config("SHEET_URL")
    credentials_path = "configuration/classicfood.json"
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
    gc = gspread.authorize(credentials)
    sh = gc.open_by_url(sheet_url)
    return sh


async def set_default_commands(dp):
    await dp.bot.set_my_commands([
        types.BotCommand("start", "Начало работы с ботом")
    ])


def register_handlers(dp: Dispatcher):
    reg_handlers(dp)
    reg_registration_individuals(dp)
    reg_registration_company(dp)
    reg_profile(dp)
    reg_order_complex(dp)
    reg_order_custom(dp)
    reg_basket(dp)
