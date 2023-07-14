import re
import string
import random
import decouple

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.utils.exceptions import MessageToDeleteNotFound, MessageIdentifierNotSpecified

from database import db_company
from keyboards import inline, reply


class RegistrationCompany(StatesGroup):
    name = State()
    address = State()
