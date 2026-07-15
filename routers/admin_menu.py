"""Вложенное административное меню и выбор пользователя для действий."""
from math import ceil

from aiogram import F, Router, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from access_control import is_group_admin
from config import CHANNEL_ID, bot
from database import company, find_return_ID, id, load_bd, phone
from keyboards import (
    get_admin_companies_keyboard,
    get_admin_database_keyboard,
    get_admin_main_keyboard,
    get_admin_service_keyboard,
)
from logging_module import root_logger
from services import get_group_member, get_recent_passes_for_user, list_group_members

router = Router()
UNREGISTERED_PAGE_SIZE = 8
RECENT_PASSES_LIMIT = 5
SEARCH_RESULTS_LIMIT = 12


class AdminMenuForm(StatesGroup):
    user_search = State()


class GroupAdminFilter(BaseFilter):
    async def __call__(self, event: types.Message | types.CallbackQuery) -> bool:
        return bool(
            event.from_user
            and await is_group_admin(
                event.from_user.id,
                user=event.from_user,
                log_denied=True,
            )
        )


router.message.filter(GroupAdminFilter())
router.callback_query.filter(GroupAdminFilter())


async def edit_or_answer(
    query: types.CallbackQuery,
    text: str,
    reply_markup: types.InlineKeyboardMarkup,
) -> None:
    try:
        await query.message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest:
        await query.message.answer(text, reply_markup=reply_markup)


def user_search_keyboard():
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(
        text="Показать незарегистрированных",
        callback_data="adm_unregistered_page_0",
    ))
    kb.row(types.InlineKeyboardButton(
        text="⬅️ В главное меню",
        callback_data="adm_back_main",
    ))
    return kb.as_markup()


def user_actions_keyboard(user_id: int, status: str):
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(
        text="Открыть профиль Telegram",
        url=f"tg://user?id={user_id}",
    ))
    kb.row(types.InlineKeyboardButton(
        text="✏️ Изменить данные",
        callback_data=f"adm_edit_user_menu_{user_id}",
    ))
    kb.row(types.InlineKeyboardButton(
        text="✉️ Отправить сообщение",
        callback_data=f"adm_message_{user_id}",
    ))

    if status in {"member", "restricted"}:
        kb.row(types.InlineKeyboardButton(
            text="🗑 Удалить из группы и БД",
            callback_data=f"adm_user_delete_{user_id}",
        ))
        kb.row(types.InlineKeyboardButton(
            text="🚫 Заблокировать и удалить из БД",
            callback_data=f"adm_user_ban_{user_id}",
        ))
    elif status == "kicked":
        kb.row(types.InlineKeyboardButton(
            text="Разблокировать в группе",
            callback_data=f"adm_unban_{user_id}",
        ))
        kb.row(types.InlineKeyboardButton(
            text="Удалить регистрацию из БД",
            callback_data=f"adm_delete_registration_{user_id}",
        ))
    elif status not in {"administrator", "creator"}:
        kb.row(types.InlineKeyboardButton(
            text="Удалить регистрацию из БД",
            callback_data=f"adm_delete_registration_{user_id}",
        ))

    kb.row(types.InlineKeyboardButton(
        text="🔎 Найти другого пользователя",
        callback_data="adm_users_menu",
    ))
    kb.row(types.InlineKeyboardButton(
        text="⬅️ В главное меню",
        callback_data="adm_back_main",
    ))
    return kb.as_markup()


def edit_user_keyboard(user_id: int):
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(
        text="Изменить компанию и ФИО",
        callback_data=f"adm_edit_company_{user_id}",
    ))
    kb.row(types.InlineKeyboardButton(
        text="Изменить телефон",
        callback_data=f"adm_edit_phone_{user_id}",
    ))
    kb.row(types.InlineKeyboardButton(
        text="⬅️ К действиям пользователя",
        callback_data=f"adm_select_user_{user_id}",
    ))
    return kb.as_markup()


def confirmation_keyboard(action: str, user_id: int):
    kb = InlineKeyboardBuilder()
    kb.add(types.InlineKeyboardButton(
        text="Подтвердить",
        callback_data=f"adm_confirm_{action}_{user_id}",
    ))
    kb.add(types.InlineKeyboardButton(
        text="Отмена",
        callback_data=f"adm_select_user_{user_id}",
    ))
    kb.adjust(2)
    return kb.as_markup()


def find_registered_matches(search_text: str) -> list[int]:
    load_bd()
    value = search_text.strip().casefold()
    if not value:
        return []

    if value.isdigit():
        index = find_return_ID(value)
        return [index] if index != -1 else []

    matches = []
    for index in range(1, len(id)):
        if value in str(company[index]).casefold():
            matches.append(index)
    return matches


def search_results_keyboard(matches: list[int]):
    kb = InlineKeyboardBuilder()
    for index in matches[:SEARCH_RESULTS_LIMIT]:
        label = str(company[index]).strip()
        if len(label) > 42:
            label = f"{label[:39]}..."
        kb.row(types.InlineKeyboardButton(
            text=f"{label} · ID {id[index]}",
            callback_data=f"adm_select_user_{id[index]}",
        ))
    kb.row(types.InlineKeyboardButton(
        text="🔎 Новый поиск",
        callback_data="adm_users_menu",
    ))
    kb.row(types.InlineKeyboardButton(
        text="⬅️ В главное меню",
        callback_data="adm_back_main",
    ))
    return kb.as_markup()


def get_unregistered_members() -> list[tuple[int, dict]]:
    load_bd()
    registered_ids = {str(item) for item in id if item != "None"}
    result = []
    for user_id_text, member_info in list_group_members().items():
        if user_id_text in registered_ids:
            continue
        try:
            result.append((int(user_id_text), member_info))
        except ValueError:
            root_logger.warning(
                f"Некорректный ID в group_members.json: {user_id_text!r}"
            )
    result.sort(key=lambda item: (item[1].get("full_name") or "").casefold())
    return result


def unregistered_page(unregistered: list[tuple[int, dict]], page: int):
    total_pages = max(1, ceil(len(unregistered) / UNREGISTERED_PAGE_SIZE))
    page = min(max(page, 0), total_pages - 1)
    start = page * UNREGISTERED_PAGE_SIZE
    items = unregistered[start:start + UNREGISTERED_PAGE_SIZE]

    lines = [
        "Незарегистрированные участники группы:",
        f"Страница {page + 1} из {total_pages}",
        "",
    ]
    kb = InlineKeyboardBuilder()
    for user_id, member_info in items:
        full_name = member_info.get("full_name") or "Имя не указано"
        username = member_info.get("username") or "нет username"
        lines.append(f"• {full_name} · {username} · ID {user_id}")
        button_name = full_name if len(full_name) <= 28 else f"{full_name[:25]}..."
        kb.row(types.InlineKeyboardButton(
            text=f"Исключить: {button_name}",
            callback_data=f"adm_unregistered_remove_{user_id}",
        ))

    navigation = []
    if page > 0:
        navigation.append(types.InlineKeyboardButton(
            text="⬅️",
            callback_data=f"adm_unregistered_page_{page - 1}",
        ))
    if page < total_pages - 1:
        navigation.append(types.InlineKeyboardButton(
            text="➡️",
            callback_data=f"adm_unregistered_page_{page + 1}",
        ))
    if navigation:
        kb.row(*navigation)
    kb.row(types.InlineKeyboardButton(
        text="🔎 Поиск зарегистрированного",
        callback_data="adm_users_menu",
    ))
    kb.row(types.InlineKeyboardButton(
        text="⬅️ В главное меню",
        callback_data="adm_back_main",
    ))
    return "\n".join(lines), kb.as_markup()


async def show_user_profile(message: types.Message, user_id: int) -> None:
    load_bd()
    index = find_return_ID(str(user_id))
    if index == -1:
        await message.answer(
            "Пользователь больше не найден в БД.",
            reply_markup=user_search_keyboard(),
        )
        return

    status = "неизвестно"
    username = "не указан"
    telegram_name = "не указано"
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        status = member.status
        username = f"@{member.user.username}" if member.user.username else "не указан"
        telegram_name = member.user.full_name
    except TelegramBadRequest as exc:
        root_logger.info(f"Не удалось получить профиль user_id={user_id}: {exc}")
        cached = get_group_member(user_id)
        if cached:
            cached_username = cached.get("username")
            username = f"@{cached_username}" if cached_username else "не указан"
            telegram_name = cached.get("full_name") or "не указано"

    joined_at = "неизвестна"
    cached = get_group_member(user_id)
    if cached and cached.get("joined_at"):
        joined_at = cached["joined_at"]

    recent = get_recent_passes_for_user(user_id, limit=RECENT_PASSES_LIMIT)
    recent_text = "\n".join(f"• {line}" for line in recent) if recent else "Нет данных."
    await message.answer(
        "Пользователь найден. Выберите действие:\n\n"
        f"ID: {user_id}\n"
        f"Username: {username}\n"
        f"Имя Telegram: {telegram_name}\n"
        f"Запись в БД: {company[index]} {phone[index]}\n"
        f"Статус в группе: {status}\n"
        f"Дата вступления: {joined_at}\n"
        f"Последние заявки на пропуск:\n{recent_text}",
        reply_markup=user_actions_keyboard(user_id, status),
    )


@router.callback_query(F.data.in_({"admins", "adm_back_main"}))
async def show_main_menu(query: types.CallbackQuery, state: FSMContext):
    await query.answer()
    await state.clear()
    text = "Администраторское меню. Выберите раздел:"
    keyboard = get_admin_main_keyboard().as_markup()
    if query.data == "admins":
        await query.message.answer(text, reply_markup=keyboard)
    else:
        await edit_or_answer(query, text, keyboard)


@router.callback_query(F.data == "adm_users_menu")
async def user_search_prompt(query: types.CallbackQuery, state: FSMContext):
    await query.answer()
    await state.clear()
    await query.message.answer(
        "Введите Telegram ID, название компании или фамилию пользователя из БД.",
        reply_markup=user_search_keyboard(),
    )
    await state.set_state(AdminMenuForm.user_search)


@router.message(AdminMenuForm.user_search)
async def user_search(message: types.Message, state: FSMContext):
    matches = find_registered_matches(message.text or "")
    await state.clear()

    if len(matches) == 1:
        await show_user_profile(message, int(id[matches[0]]))
        return

    if len(matches) > 1:
        shown = min(len(matches), SEARCH_RESULTS_LIMIT)
        suffix = "" if len(matches) <= SEARCH_RESULTS_LIMIT else f" Показаны первые {shown}."
        await message.answer(
            f"Найдено совпадений: {len(matches)}.{suffix} Выберите пользователя:",
            reply_markup=search_results_keyboard(matches),
        )
        return

    unregistered = get_unregistered_members()
    if not unregistered:
        await message.answer(
            "Пользователь не найден в БД. Незарегистрированных участников группы нет.",
            reply_markup=user_search_keyboard(),
        )
        return

    text, keyboard = unregistered_page(unregistered, 0)
    await message.answer(
        "Пользователь не найден в БД.\n\n" + text,
        reply_markup=keyboard,
    )


@router.callback_query(lambda callback: callback.data and callback.data.startswith("adm_select_user_"))
async def select_user(query: types.CallbackQuery):
    await query.answer()
    user_id = int(query.data.rsplit("_", 1)[-1])
    await show_user_profile(query.message, user_id)


@router.callback_query(lambda callback: callback.data and callback.data.startswith("adm_edit_user_menu_"))
async def edit_user_menu(query: types.CallbackQuery):
    await query.answer()
    user_id = int(query.data.rsplit("_", 1)[-1])
    await query.message.answer(
        f"Какие данные изменить у пользователя ID {user_id}?",
        reply_markup=edit_user_keyboard(user_id),
    )


@router.callback_query(lambda callback: callback.data and callback.data.startswith("adm_user_delete_"))
async def delete_user_prompt(query: types.CallbackQuery):
    await query.answer()
    user_id = int(query.data.rsplit("_", 1)[-1])
    await query.message.answer(
        f"Удалить пользователя ID {user_id} из группы и удалить его регистрацию из БД?",
        reply_markup=confirmation_keyboard("remove", user_id),
    )


@router.callback_query(lambda callback: callback.data and callback.data.startswith("adm_user_ban_"))
async def ban_user_prompt(query: types.CallbackQuery):
    await query.answer()
    user_id = int(query.data.rsplit("_", 1)[-1])
    await query.message.answer(
        f"Заблокировать пользователя ID {user_id} в группе и удалить его регистрацию из БД?",
        reply_markup=confirmation_keyboard("ban", user_id),
    )


@router.callback_query(lambda callback: callback.data and callback.data.startswith("adm_unregistered_page_"))
async def unregistered_members_page(query: types.CallbackQuery):
    await query.answer()
    page = int(query.data.rsplit("_", 1)[-1])
    unregistered = get_unregistered_members()
    if not unregistered:
        await edit_or_answer(
            query,
            "Незарегистрированных участников группы нет.",
            user_search_keyboard(),
        )
        return
    text, keyboard = unregistered_page(unregistered, page)
    await edit_or_answer(query, text, keyboard)


@router.callback_query(lambda callback: callback.data and callback.data.startswith("adm_unregistered_remove_"))
async def unregistered_remove_prompt(query: types.CallbackQuery):
    await query.answer()
    user_id = int(query.data.rsplit("_", 1)[-1])
    member_info = get_group_member(user_id) or {}
    full_name = member_info.get("full_name") or "Имя не указано"
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(
        text="Открыть профиль Telegram",
        url=f"tg://user?id={user_id}",
    ))
    kb.row(types.InlineKeyboardButton(
        text="Подтвердить исключение",
        callback_data=f"adm_confirm_remove_{user_id}",
    ))
    kb.row(types.InlineKeyboardButton(
        text="Отмена",
        callback_data="adm_unregistered_page_0",
    ))
    await query.message.answer(
        "Пользователь не зарегистрирован в БД.\n"
        f"Имя: {full_name}\nID: {user_id}\n\n"
        "Исключить его из группы?",
        reply_markup=kb.as_markup(),
    )


@router.callback_query(F.data == "adm_service_menu")
async def service_menu(query: types.CallbackQuery):
    await query.answer()
    await edit_or_answer(
        query,
        "Сервисные функции:",
        get_admin_service_keyboard().as_markup(),
    )


@router.callback_query(F.data == "adm_database_menu")
async def database_menu(query: types.CallbackQuery):
    await query.answer()
    await edit_or_answer(
        query,
        "Работа с базой данных:",
        get_admin_database_keyboard().as_markup(),
    )


@router.callback_query(F.data == "adm_companies_menu")
async def companies_menu(query: types.CallbackQuery):
    await query.answer()
    await edit_or_answer(
        query,
        "Работа со списками компаний:",
        get_admin_companies_keyboard().as_markup(),
    )
