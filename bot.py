import asyncio
import logging
from aiogram import Dispatcher
from config import bot, bot_commands
from services import reset_sent_messages
from routers import user, admin, events
# Импортируем, чтобы запустить конфигурацию логгера
import logging_module

dp = Dispatcher()
dp.include_router(user.router)
dp.include_router(admin.router)
dp.include_router(events.router)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_my_commands(bot_commands)
    asyncio.create_task(reset_sent_messages())
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logging.exception(e)
        print(e)

