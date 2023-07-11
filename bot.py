from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from configuration import settings

import asyncio
import logging


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format=u'[%(asctime)s] - %(message)s')
    settings.logger.info("Starting bot")

    bot = Bot(settings.bot_token, parse_mode="HTML")
    storage = MemoryStorage()
    dp = Dispatcher(bot, storage=storage)
    settings.register_handlers(dp)

    await settings.set_default_commands(dp)
    await dp.start_polling()

if __name__ == "__main__":
    asyncio.run(main())
