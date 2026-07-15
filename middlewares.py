"""Общие middleware проверки доступа и административных действий."""
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from access_control import get_member_status, is_group_admin, log_access_denied

ADMIN_CALLBACKS = {
    "admins", "edit_bd", "reg", "cat_bd", "find_bd", "user_profile",
    "company_list", "unregistered_members", "del_bd", "cat_log", "cat_KPP",
    "phone", "load_bd",
}
ADMIN_PREFIXES = ("adm_", "del_users_from_group_")
ADMIN_STATES = {
    "Form:adm_find", "Form:edit_db_new", "Form:edit_db_old", "Form:del_elm",
    "Form:adm_user_profile", "Form:adm_company_list",
    "AdminUserForm:find", "AdminUserForm:profile", "AdminUserForm:edit_company",
    "AdminUserForm:edit_phone", "AdminUserForm:message_text", "AdminUserForm:message_confirm",
    "AdminMenuForm:user_search",
}


class GroupAccessMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, Message):
            if event.chat.type != "private" or event.from_user is None:
                return await handler(event, data)
            user = event.from_user
            action = "private_message"
        elif isinstance(event, CallbackQuery):
            if event.from_user is None:
                return await handler(event, data)
            if event.message is not None and event.message.chat.type != "private":
                return await handler(event, data)
            user = event.from_user
            action = "private_callback"
        else:
            return await handler(event, data)

        allowed, status = await get_member_status(user.id)
        if allowed:
            return await handler(event, data)

        log_access_denied(user, action, status)
        if isinstance(event, CallbackQuery):
            await event.answer("Доступ запрещен", show_alert=True)
        else:
            await event.answer(
                "Доступ запрещен. Вы должны состоять в специальной группе "
                "для доступа к функциям бота."
            )
        return None


class AdminAccessMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        requires_admin = False
        if isinstance(event, CallbackQuery) and event.data:
            requires_admin = event.data in ADMIN_CALLBACKS or event.data.startswith(ADMIN_PREFIXES)
        elif isinstance(event, Message):
            requires_admin = data.get("raw_state") in ADMIN_STATES

        if not requires_admin or event.from_user is None:
            return await handler(event, data)

        if await is_group_admin(event.from_user.id, user=event.from_user, log_denied=True):
            return await handler(event, data)

        if isinstance(event, CallbackQuery):
            await event.answer("Административные права отсутствуют", show_alert=True)
        else:
            await event.answer("Административные права отсутствуют.")
        return None
