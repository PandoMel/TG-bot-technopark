"""
Роутер для событий группы (join/leave)
aiogram 3.14
"""
from aiogram import Router, Bot
from aiogram.filters import ChatMemberUpdatedFilter, IS_NOT_MEMBER, IS_MEMBER
from aiogram.types import ChatMemberUpdated
from config import ADMINS
from services import add_group_member, remove_group_member

router = Router()

@router.chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_NOT_MEMBER >> IS_MEMBER))
async def user_joined_chat(event: ChatMemberUpdated, bot: Bot):
    admin_ids = ADMINS
    user = event.new_chat_member.user
    user_id = user.id
    add_group_member(user)
    username = f"@{user.username}" if user.username else "отсутствует"
    full_name = user.full_name
    chat_id = event.chat.id
    message_sms = (
        f"Новый пользователь вступил в чат:\n"
        f"ID: {user_id}\n"
        f"ChatID: {chat_id}\n"
        f"Name: {username}, full: {full_name}"
    )
    for admin_id in admin_ids:
        try:
            await bot.send_message(admin_id, message_sms)
        except Exception as e:
            print(f"Не удалось отправить сообщение администратору {admin_id}: {e}")

@router.chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_MEMBER >> IS_NOT_MEMBER))
async def user_left_chat(event: ChatMemberUpdated, bot: Bot):
    admin_ids = ADMINS
    user = event.new_chat_member.user
    user_id = user.id
    remove_group_member(user_id)
    username = f"@{user.username}" if user.username else "Имя отсутствует"
    full_name = user.full_name
    chat_id = event.chat.id
    message_sms = (
        f"Пользователь покинул чат:\n"
        f"ID: {user_id}\n"
        f"ChatID: {chat_id}\n"
        f"Name: {username}, full: {full_name}"
    )
    for admin_id in admin_ids:
        try:
            await bot.send_message(admin_id, message_sms)
        except Exception as e:
            print(f"Не удалось отправить сообщение администратору {admin_id}: {e}")
