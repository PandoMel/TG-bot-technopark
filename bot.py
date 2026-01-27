import asyncio
import logging
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.exceptions import TelegramBadRequest

from config import bot_token, ADMINS, OHRANA_ID, CHANNEL_ID
from logging_module import setup_logging
from database import load_bd

# Импорт роутеров
from routers.user import router as user_router
from routers.admin import router as admin_router
from routers.events import router as events_router

# Инициализация бота
dp = Dispatcher()
bot = Bot(token=bot_token)

# Настройка логирования
root_logger, ohrana_logger = setup_logging()

# Загрузка БД
load_bd()

# Словарь для отслеживания времени отправки сообщений (антидубликат)
sent_messages = {}
TIME_WINDOW = timedelta(minutes=30)


async def set_bot_commands():
    """Установка команд бота"""
    bot_commands = [
        BotCommand(command="start", description="Запуск"),
        BotCommand(command="status", description="Статус доступа"),
        BotCommand(command="help", description="Помощь")
    ]
    await bot.set_my_commands(bot_commands)


async def on_startup(dispatcher: Dispatcher):
    """При запуске бота"""
    await set_bot_commands()
    root_logger.info("Бот запущен")


async def on_shutdown(dispatcher: Dispatcher):
    """При остановке бота"""
    root_logger.info("Бот остановлен")


async def main():
    """Основная функция"""
    
    # Регистрация роутеров
    dp.include_router(user_router)
    dp.include_router(admin_router)
    dp.include_router(events_router)
    
    # Startup и shutdown обработчики
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Запуск polling
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
