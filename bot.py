import asyncio
import logging

from aiogram import Dispatcher

from access_control import sync_known_group_members
from config import bot, bot_commands
from middlewares import AdminAccessMiddleware, GroupAccessMiddleware
from routers import admin, admin_users, events, fallback, user
from services import reset_sent_messages

# Импортируем, чтобы запустить конфигурацию логгера
import logging_module


dp = Dispatcher()
dp.message.outer_middleware(GroupAccessMiddleware())
dp.message.outer_middleware(AdminAccessMiddleware())
dp.callback_query.outer_middleware(GroupAccessMiddleware())
dp.callback_query.outer_middleware(AdminAccessMiddleware())
dp.include_router(user.router)
dp.include_router(admin_users.router)
dp.include_router(admin.router)
dp.include_router(events.router)
dp.include_router(fallback.router)


async def main():
    # Старые callback-обновления после перезапуска намеренно удаляются.
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_my_commands(bot_commands)
    await sync_known_group_members()
    asyncio.create_task(reset_sent_messages())
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped by KeyboardInterrupt")
    except Exception:
        logging.exception("Bot crashed on startup")
        raise
