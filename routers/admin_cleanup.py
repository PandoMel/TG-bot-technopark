"""Связанное удаление пользователя из группы и Legacy БД."""
from aiogram import Router, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import BaseFilter

from access_control import is_group_admin
from config import CHANNEL_ID, bot
from logging_module import root_logger
from services import delete_registration_by_user_id, remove_group_member

router = Router()


class GroupAdminFilter(BaseFilter):
    async def __call__(self, event: types.CallbackQuery) -> bool:
        return bool(
            event.from_user
            and await is_group_admin(event.from_user.id, user=event.from_user, log_denied=True)
        )


router.callback_query.filter(GroupAdminFilter())


def user_id_from_callback(data: str) -> int:
    return int(data.rsplit("_", 1)[-1])


@router.callback_query(lambda callback: callback.data and callback.data.startswith("adm_confirm_remove_"))
async def confirm_remove(query: types.CallbackQuery):
    await query.answer()
    user_id = user_id_from_callback(query.data)
    try:
        await bot.ban_chat_member(CHANNEL_ID, user_id)
        await bot.unban_chat_member(CHANNEL_ID, user_id, only_if_banned=True)
    except TelegramBadRequest as exc:
        await query.message.answer(f"Не удалось удалить пользователя: {exc}")
        return

    remove_group_member(user_id)
    registration_deleted = delete_registration_by_user_id(user_id)
    root_logger.warning(
        f"ADMIN_USER_REMOVED admin_id={query.from_user.id} target_id={user_id} "
        f"registration_deleted={registration_deleted}"
    )
    await query.message.answer(
        "Пользователь удален из группы. "
        + ("Регистрация удалена из БД." if registration_deleted else "Регистрация в БД не найдена.")
    )


@router.callback_query(lambda callback: callback.data and callback.data.startswith("adm_confirm_ban_"))
async def confirm_ban(query: types.CallbackQuery):
    await query.answer()
    user_id = user_id_from_callback(query.data)
    try:
        await bot.ban_chat_member(CHANNEL_ID, user_id)
    except TelegramBadRequest as exc:
        await query.message.answer(f"Не удалось заблокировать пользователя: {exc}")
        return

    remove_group_member(user_id)
    registration_deleted = delete_registration_by_user_id(user_id)
    root_logger.warning(
        f"ADMIN_USER_BANNED admin_id={query.from_user.id} target_id={user_id} "
        f"registration_deleted={registration_deleted}"
    )
    await query.message.answer(
        "Пользователь заблокирован в группе. "
        + ("Регистрация удалена из БД." if registration_deleted else "Регистрация в БД не найдена.")
    )
