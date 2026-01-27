"""
Роутер для событий группы (join/leave)
aiogram 3.14
"""
from aiogram import Router, types
from aiogram.filters import ChatMemberUpdatedFilter
from aiogram.types import ChatMemberUpdated, ChatMemberMember

from config import CHANNEL_ID
from logging_module import get_root_logger

router = Router()
root_logger = get_root_logger()


@router.my_chat_member(ChatMemberUpdatedFilter(
    member_status_changed=True
))
async def my_chat_member_handler(update: ChatMemberUpdated):
    """Обработка событий join/leave группы"""
    
    if update.new_chat_member.status == 'member':
        # Бот добавлен в группу
        root_logger.info(f"Bot joined group {update.chat.title} (id: {update.chat.id})")
    
    elif update.new_chat_member.status == 'left':
        # Бот удален из группы
        root_logger.info(f"Bot left group {update.chat.title} (id: {update.chat.id})")
