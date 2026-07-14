"""Проверка доступа и синхронизация известных участников основной группы."""
import asyncio

from aiogram import types
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter

from config import CHANNEL_ID, bot
from database import id as database_user_ids, load_bd
from logging_module import root_logger
from services import add_group_member, list_group_members, remove_group_member

ADMIN_STATUSES = {"administrator", "creator"}
MEMBER_STATUSES = {"member", "administrator", "creator"}


def member_has_access(member) -> bool:
    if member.status in MEMBER_STATUSES:
        return True
    if member.status == "restricted":
        return bool(getattr(member, "is_member", False))
    return False


async def get_member_status(user_id: int) -> tuple[bool, str]:
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
    except TelegramBadRequest as exc:
        root_logger.info(f"Не удалось проверить доступ user_id={user_id}: {exc}")
        return False, "unknown"
    except Exception as exc:
        root_logger.error(f"Ошибка проверки доступа user_id={user_id}: {exc}")
        return False, "error"
    return member_has_access(member), member.status


def log_access_denied(user: types.User, action: str, status: str) -> None:
    username = f"@{user.username}" if user.username else "отсутствует"
    root_logger.info(
        "ACCESS_DENIED "
        f"action={action} user_id={user.id} username={username} "
        f"full_name={user.full_name!r} status={status}"
    )


async def is_group_admin(user_id: int, user: types.User | None = None, log_denied: bool = False) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
    except Exception as exc:
        root_logger.error(f"Ошибка проверки прав администратора user_id={user_id}: {exc}")
        return False

    allowed = member.status in ADMIN_STATUSES
    if log_denied and not allowed and user is not None:
        username = f"@{user.username}" if user.username else "отсутствует"
        root_logger.warning(
            "ADMIN_ACCESS_DENIED "
            f"user_id={user.id} username={username} full_name={user.full_name!r} "
            f"status={member.status}"
        )
    return allowed


async def get_group_administrators() -> list[types.User]:
    try:
        administrators = await bot.get_chat_administrators(CHANNEL_ID)
    except Exception as exc:
        root_logger.error(f"Не удалось получить список администраторов группы: {exc}")
        return []
    return [member.user for member in administrators if not member.user.is_bot]


async def sync_known_group_members() -> None:
    """Сверяет зарегистрированных и ранее замеченных пользователей при запуске."""
    load_bd()
    known_ids = {str(item) for item in database_user_ids if item != "None"}
    known_ids.update(list_group_members().keys())
    for administrator in await get_group_administrators():
        known_ids.add(str(administrator.id))

    checked = active = removed = errors = 0
    for user_id_text in sorted(known_ids):
        try:
            user_id = int(user_id_text)
        except ValueError:
            root_logger.warning(f"Некорректный ID при синхронизации: {user_id_text!r}")
            errors += 1
            continue

        try:
            member = await bot.get_chat_member(CHANNEL_ID, user_id)
        except TelegramRetryAfter as exc:
            await asyncio.sleep(exc.retry_after)
            try:
                member = await bot.get_chat_member(CHANNEL_ID, user_id)
            except Exception as retry_exc:
                root_logger.warning(f"Ошибка повторной синхронизации user_id={user_id}: {retry_exc}")
                errors += 1
                continue
        except Exception as exc:
            root_logger.warning(f"Ошибка синхронизации user_id={user_id}: {exc}")
            errors += 1
            continue

        checked += 1
        if member_has_access(member):
            add_group_member(member.user)
            active += 1
        else:
            remove_group_member(user_id)
            removed += 1
        await asyncio.sleep(0.05)

    root_logger.info(
        "Синхронизация участников завершена: "
        f"проверено={checked}, в_группе={active}, удалено_из_json={removed}, ошибок={errors}"
    )
