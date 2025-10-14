import asyncio
import logging

from aiogram import Bot, Dispatcher

from src.config import settings
from src.core.logging_config import setup_logging
from src.handlers import register_handlers


async def main() -> None:
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting bot...")

    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()
    register_handlers(dp)

    logger.info("Bot is polling...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
