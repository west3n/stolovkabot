import re
import decouple

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.utils.exceptions import MessageToDeleteNotFound, MessageIdentifierNotSpecified

from keyboards import inline, reply


class RegistrationCompany(StatesGroup):
    name = State()
    address = State()
