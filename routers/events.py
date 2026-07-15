"""Роутер событий входа и выхода участников основной группы."""
from aiogram import Bot, Router
from aiogram.filters import ChatMemberUpdatedFilter, IS_MEMBER, IS_NOT_MEMBER
from aiogram.types import ChatMemberUpdated, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from access_control import get_group_administrators
from config import CHANNEL_ID
from logging_module import root_logger
from services import add_group_member, delete_registration_by_user_id, remove_group_member

router = Router()


def event_keyboard(user_id: int):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="Открыть профиль", url=f"tg://user?id={user_id}"))
    keyboard.add(InlineKeyboardButton(text="Управление пользователем", callback_data=f"adm_profile_{user_id}"))
    keyboard.adjust(1)
    return keyboard.as_markup()


async def notify_administrators(bot: Bot, text: str, user_id: int) -> None:
    for administrator in await get_group_administrators():
        try:
            await bot.send_message(administrator.id, text, reply_markup=event_keyboard(user_id))
        except Exception as exc:
            root_logger.info(
                f"Не удалось отправить уведомление администратору {administrator.id}: {exc}"
            )


@router.chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_NOT_MEMBER >> IS_MEMBER))
async def user_joined_chat(event: ChatMemberUpdated, bot: Bot):
    if event.chat.id != CHANNEL_ID:
        return

    user = event.new_chat_member.user
    actor = event.from_user
    add_group_member(user)
    username = f"@{user.username}" if user.username else "отсутствует"

    root_logger.info(
        "GROUP_MEMBER_JOINED "
        f"user_id={user.id} username={username} full_name={user.full_name!r} "
        f"actor_id={actor.id} actor_name={actor.full_name!r}"
    )
    await notify_administrators(
        bot,
        "Новый пользователь вступил в чат:\n"
        f"ID: {user.id}\nUsername: {username}\nИмя: {user.full_name}\n"
        f"Добавил/вступил: {actor.full_name}, ID: {actor.id}",
        user.id,
    )


@router.chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_MEMBER >> IS_NOT_MEMBER))
async def user_left_chat(event: ChatMemberUpdated, bot: Bot):
    if event.chat.id != CHANNEL_ID:
        return

    user = event.new_chat_member.user
    actor = event.from_user
    remove_group_member(user.id)
    registration_deleted = delete_registration_by_user_id(user.id)
    username = f"@{user.username}" if user.username else "отсутствует"

    if actor.id == user.id:
        reason = "вышел самостоятельно"
    elif actor.is_bot:
        reason = f"исключен ботом {actor.full_name}, ID: {actor.id}"
    else:
        reason = f"исключен администратором {actor.full_name}, ID: {actor.id}"

    root_logger.warning(
        "GROUP_MEMBER_LEFT "
        f"user_id={user.id} username={username} full_name={user.full_name!r} "
        f"reason={reason!r} old_status={event.old_chat_member.status} "
        f"new_status={event.new_chat_member.status} "
        f"registration_deleted={registration_deleted}"
    )
    await notify_administrators(
        bot,
        "Пользователь покинул чат:\n"
        f"ID: {user.id}\nUsername: {username}\nИмя: {user.full_name}\n"
        f"Причина: {reason}\n"
        f"Регистрация в БД: {'удалена' if registration_deleted else 'не найдена'}",
        user.id,
    )
