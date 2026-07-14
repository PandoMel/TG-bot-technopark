"""Управление пользователями из админ-панели без изменения Legacy БД."""
from aiogram import F, Router, types
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramRetryAfter
from aiogram.filters import BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from access_control import is_group_admin
from config import CHANNEL_ID, bot
from database import company, del_bd, find_by_name, find_return_ID, id, load_bd, phone, save_bd
from logging_module import root_logger
from services import get_group_member, get_recent_passes_for_user, remove_group_member

router = Router()
RECENT_PASSES_LIMIT = 5
MAX_MESSAGE_LENGTH = 3500


class AdminUserForm(StatesGroup):
    find = State()
    profile = State()
    edit_company = State()
    edit_phone = State()
    message_text = State()
    message_confirm = State()


class GroupAdminFilter(BaseFilter):
    async def __call__(self, event: types.Message | types.CallbackQuery) -> bool:
        return bool(
            event.from_user
            and await is_group_admin(event.from_user.id, user=event.from_user, log_denied=True)
        )


router.message.filter(GroupAdminFilter())
router.callback_query.filter(GroupAdminFilter())


def user_id_from_callback(data: str) -> int:
    return int(data.rsplit("_", 1)[-1])


def profile_keyboard(user_id: int, registered: bool, status: str):
    keyboard = InlineKeyboardBuilder()
    keyboard.row(types.InlineKeyboardButton(text="Открыть профиль Telegram", url=f"tg://user?id={user_id}"))
    keyboard.row(types.InlineKeyboardButton(text="Написать сообщение", callback_data=f"adm_message_{user_id}"))
    if registered:
        keyboard.row(types.InlineKeyboardButton(text="Изменить компанию и ФИО", callback_data=f"adm_edit_company_{user_id}"))
        keyboard.row(types.InlineKeyboardButton(text="Изменить телефон", callback_data=f"adm_edit_phone_{user_id}"))
        keyboard.row(types.InlineKeyboardButton(text="Удалить регистрацию из БД", callback_data=f"adm_delete_registration_{user_id}"))

    if status == "kicked":
        keyboard.row(types.InlineKeyboardButton(text="Разблокировать в группе", callback_data=f"adm_unban_{user_id}"))
    elif status in {"member", "administrator", "creator", "restricted"}:
        keyboard.row(types.InlineKeyboardButton(text="Удалить из группы", callback_data=f"adm_remove_{user_id}"))
        keyboard.row(types.InlineKeyboardButton(text="Заблокировать в группе", callback_data=f"adm_ban_{user_id}"))
    else:
        keyboard.row(types.InlineKeyboardButton(text="Заблокировать вход в группу", callback_data=f"adm_ban_{user_id}"))
    return keyboard.as_markup()


def confirm_keyboard(action: str, user_id: int):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(types.InlineKeyboardButton(text="Подтвердить", callback_data=f"adm_confirm_{action}_{user_id}"))
    keyboard.add(types.InlineKeyboardButton(text="Отмена", callback_data="adm_action_cancel"))
    keyboard.adjust(2)
    return keyboard.as_markup()


def message_confirm_keyboard(user_id: int):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(types.InlineKeyboardButton(text="Отправить", callback_data=f"adm_message_send_{user_id}"))
    keyboard.add(types.InlineKeyboardButton(text="Отмена", callback_data="adm_action_cancel"))
    keyboard.adjust(2)
    return keyboard.as_markup()


async def show_profile(message: types.Message, user_id: int) -> None:
    load_bd()
    index = find_return_ID(str(user_id))
    registered = index != -1
    status = "неизвестно"
    username = "не указан"
    full_name = "не указано"

    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        status = member.status
        username = f"@{member.user.username}" if member.user.username else "не указан"
        full_name = member.user.full_name
    except TelegramBadRequest as exc:
        root_logger.info(f"Не удалось получить профиль user_id={user_id}: {exc}")
        cached = get_group_member(user_id)
        if cached:
            cached_username = cached.get("username")
            username = f"@{cached_username}" if cached_username else "не указан"
            full_name = cached.get("full_name") or "не указано"

    database_text = f"{company[index]} {phone[index]}" if registered else "регистрация отсутствует"
    joined_at = "неизвестна"
    cached = get_group_member(user_id)
    if cached and cached.get("joined_at"):
        joined_at = cached["joined_at"]

    recent = get_recent_passes_for_user(user_id, limit=RECENT_PASSES_LIMIT)
    recent_text = "\n".join(f"• {line}" for line in recent) if recent else "Нет данных."

    await message.answer(
        "Профиль пользователя:\n"
        f"ID: {user_id}\nUsername: {username}\nИмя Telegram: {full_name}\n"
        f"Данные из БД: {database_text}\nСтатус в группе: {status}\n"
        f"Дата вступления: {joined_at}\nПоследние заявки пропусков:\n{recent_text}",
        reply_markup=profile_keyboard(user_id, registered, status),
    )


@router.callback_query(F.data == "find_bd")
async def find_prompt(query: types.CallbackQuery, state: FSMContext):
    await query.answer()
    await state.clear()
    await query.message.answer("Введите компанию, фамилию или Telegram ID пользователя.")
    await state.set_state(AdminUserForm.find)


@router.message(AdminUserForm.find)
async def find_user(message: types.Message, state: FSMContext):
    result = find_by_name((message.text or "").strip())
    await state.clear()
    if result == -2:
        await message.answer("Найдено несколько совпадений. Уточните запрос.")
    elif result == -1:
        await message.answer("Пользователь не найден в БД.")
    else:
        await show_profile(message, int(id[result]))


@router.callback_query(F.data == "user_profile")
async def profile_prompt(query: types.CallbackQuery, state: FSMContext):
    await query.answer()
    await state.clear()
    await query.message.answer("Введите Telegram ID пользователя.")
    await state.set_state(AdminUserForm.profile)


@router.message(AdminUserForm.profile)
async def profile_by_id(message: types.Message, state: FSMContext):
    await state.clear()
    value = (message.text or "").strip()
    if not value.isdigit():
        await message.answer("ID должен быть числом.")
        return
    await show_profile(message, int(value))


@router.callback_query(lambda callback: callback.data and callback.data.startswith("adm_profile_"))
async def profile_from_button(query: types.CallbackQuery):
    await query.answer()
    await show_profile(query.message, user_id_from_callback(query.data))


@router.callback_query(lambda callback: callback.data and callback.data.startswith("adm_edit_company_"))
async def edit_company_prompt(query: types.CallbackQuery, state: FSMContext):
    await query.answer()
    user_id = user_id_from_callback(query.data)
    load_bd()
    if find_return_ID(str(user_id)) == -1:
        await query.message.answer("Запись пользователя отсутствует в БД.")
        return
    await state.clear()
    await state.update_data(target_user_id=user_id)
    await query.message.answer('Введите новое значение в формате: "компания, ФИО".')
    await state.set_state(AdminUserForm.edit_company)


@router.message(AdminUserForm.edit_company)
async def edit_company_save(message: types.Message, state: FSMContext):
    new_value = (message.text or "").strip().replace("\n", " ")
    if not new_value or ";" in new_value:
        await message.answer('Значение не должно быть пустым или содержать ";".')
        return
    user_id = int((await state.get_data())["target_user_id"])
    load_bd()
    index = find_return_ID(str(user_id))
    if index == -1:
        await message.answer("Запись больше не существует.")
        await state.clear()
        return
    company[index] = new_value
    save_bd()
    root_logger.warning(f"ADMIN_DB_EDIT admin_id={message.from_user.id} target_id={user_id} field=company")
    await state.clear()
    await message.answer("Компания и ФИО обновлены.")
    await show_profile(message, user_id)


@router.callback_query(lambda callback: callback.data and callback.data.startswith("adm_edit_phone_"))
async def edit_phone_prompt(query: types.CallbackQuery, state: FSMContext):
    await query.answer()
    user_id = user_id_from_callback(query.data)
    load_bd()
    if find_return_ID(str(user_id)) == -1:
        await query.message.answer("Запись пользователя отсутствует в БД.")
        return
    await state.clear()
    await state.update_data(target_user_id=user_id)
    await query.message.answer("Введите новый телефон.")
    await state.set_state(AdminUserForm.edit_phone)


@router.message(AdminUserForm.edit_phone)
async def edit_phone_save(message: types.Message, state: FSMContext):
    new_value = (message.text or "").strip().replace("\n", " ")
    if not new_value or len(new_value) > 50 or ";" in new_value:
        await message.answer("Некорректный телефон.")
        return
    user_id = int((await state.get_data())["target_user_id"])
    load_bd()
    index = find_return_ID(str(user_id))
    if index == -1:
        await message.answer("Запись больше не существует.")
        await state.clear()
        return
    phone[index] = new_value
    save_bd()
    root_logger.warning(f"ADMIN_DB_EDIT admin_id={message.from_user.id} target_id={user_id} field=phone")
    await state.clear()
    await message.answer("Телефон обновлен.")
    await show_profile(message, user_id)


@router.callback_query(lambda callback: callback.data and callback.data.startswith("adm_message_") and not callback.data.startswith("adm_message_send_"))
async def message_prompt(query: types.CallbackQuery, state: FSMContext):
    await query.answer()
    user_id = user_id_from_callback(query.data)
    await state.clear()
    await state.update_data(target_user_id=user_id)
    await query.message.answer(f"Введите сообщение для ID {user_id}. Максимум {MAX_MESSAGE_LENGTH} символов.")
    await state.set_state(AdminUserForm.message_text)


@router.message(AdminUserForm.message_text)
async def message_preview(message: types.Message, state: FSMContext):
    text = (message.text or "").strip()
    if not text or len(text) > MAX_MESSAGE_LENGTH:
        await message.answer("Проверьте текст и его длину.")
        return
    user_id = int((await state.get_data())["target_user_id"])
    await state.update_data(message_text=text)
    await message.answer(
        f"Предпросмотр сообщения для ID {user_id}:\n\n{text}",
        reply_markup=message_confirm_keyboard(user_id),
    )
    await state.set_state(AdminUserForm.message_confirm)


@router.callback_query(lambda callback: callback.data and callback.data.startswith("adm_message_send_"))
async def message_send(query: types.CallbackQuery, state: FSMContext):
    await query.answer()
    user_id = user_id_from_callback(query.data)
    data = await state.get_data()
    if data.get("target_user_id") != user_id or not data.get("message_text"):
        await query.message.answer("Данные сообщения утеряны. Начните отправку заново.")
        await state.clear()
        return
    try:
        await bot.send_message(user_id, f"Сообщение от администрации Технопарка:\n\n{data['message_text']}")
    except TelegramForbiddenError:
        await query.message.answer("Пользователь заблокировал бота или недоступен.")
        root_logger.warning(f"ADMIN_MESSAGE_FAILED admin_id={query.from_user.id} target_id={user_id} forbidden")
    except TelegramRetryAfter as exc:
        await query.message.answer(f"Повторите через {exc.retry_after} секунд.")
    except TelegramBadRequest as exc:
        await query.message.answer(f"Сообщение не доставлено: {exc}")
    else:
        await query.message.answer("Сообщение отправлено.")
        root_logger.warning(f"ADMIN_MESSAGE_SENT admin_id={query.from_user.id} target_id={user_id}")
    await state.clear()


async def ask_confirmation(query: types.CallbackQuery, action: str, text: str):
    await query.answer()
    user_id = user_id_from_callback(query.data)
    await query.message.answer(f"{text} пользователя ID {user_id}?", reply_markup=confirm_keyboard(action, user_id))


@router.callback_query(lambda callback: callback.data and callback.data.startswith("adm_remove_"))
async def remove_prompt(query: types.CallbackQuery):
    await ask_confirmation(query, "remove", "Удалить из группы")


@router.callback_query(lambda callback: callback.data and callback.data.startswith("adm_ban_"))
async def ban_prompt(query: types.CallbackQuery):
    await ask_confirmation(query, "ban", "Заблокировать в группе")


@router.callback_query(lambda callback: callback.data and callback.data.startswith("adm_unban_"))
async def unban_prompt(query: types.CallbackQuery):
    await ask_confirmation(query, "unban", "Разблокировать")


@router.callback_query(lambda callback: callback.data and callback.data.startswith("adm_delete_registration_"))
async def delete_registration_prompt(query: types.CallbackQuery):
    await ask_confirmation(query, "delete_registration", "Удалить регистрацию из БД у")


@router.callback_query(lambda callback: callback.data and callback.data.startswith("del_users_from_group_"))
async def legacy_remove_prompt(query: types.CallbackQuery):
    await ask_confirmation(query, "remove", "Удалить из группы")


@router.callback_query(F.data == "adm_action_cancel")
async def cancel_action(query: types.CallbackQuery, state: FSMContext):
    await query.answer("Отменено")
    await state.clear()
    await query.message.edit_reply_markup(reply_markup=None)


@router.callback_query(lambda callback: callback.data and callback.data.startswith("adm_confirm_remove_"))
async def confirm_remove(query: types.CallbackQuery):
    await query.answer()
    user_id = user_id_from_callback(query.data)
    try:
        await bot.ban_chat_member(CHANNEL_ID, user_id)
        await bot.unban_chat_member(CHANNEL_ID, user_id, only_if_banned=True)
        remove_group_member(user_id)
    except TelegramBadRequest as exc:
        await query.message.answer(f"Не удалось удалить пользователя: {exc}")
        return
    root_logger.warning(f"ADMIN_USER_REMOVED admin_id={query.from_user.id} target_id={user_id}")
    await query.message.answer("Пользователь удален из группы. Регистрация сохранена.")


@router.callback_query(lambda callback: callback.data and callback.data.startswith("adm_confirm_ban_"))
async def confirm_ban(query: types.CallbackQuery):
    await query.answer()
    user_id = user_id_from_callback(query.data)
    try:
        await bot.ban_chat_member(CHANNEL_ID, user_id)
        remove_group_member(user_id)
    except TelegramBadRequest as exc:
        await query.message.answer(f"Не удалось заблокировать пользователя: {exc}")
        return
    root_logger.warning(f"ADMIN_USER_BANNED admin_id={query.from_user.id} target_id={user_id}")
    await query.message.answer("Пользователь заблокирован в группе.")


@router.callback_query(lambda callback: callback.data and callback.data.startswith("adm_confirm_unban_"))
async def confirm_unban(query: types.CallbackQuery):
    await query.answer()
    user_id = user_id_from_callback(query.data)
    try:
        await bot.unban_chat_member(CHANNEL_ID, user_id, only_if_banned=True)
    except TelegramBadRequest as exc:
        await query.message.answer(f"Не удалось разблокировать пользователя: {exc}")
        return
    root_logger.warning(f"ADMIN_USER_UNBANNED admin_id={query.from_user.id} target_id={user_id}")
    await query.message.answer("Пользователь разблокирован.")


@router.callback_query(lambda callback: callback.data and callback.data.startswith("adm_confirm_delete_registration_"))
async def confirm_delete_registration(query: types.CallbackQuery):
    await query.answer()
    user_id = user_id_from_callback(query.data)
    load_bd()
    index = find_return_ID(str(user_id))
    if index == -1:
        await query.message.answer("Регистрация уже отсутствует.")
        return
    deleted_company = company[index]
    del_bd(index)
    root_logger.warning(
        f"ADMIN_REGISTRATION_DELETED admin_id={query.from_user.id} "
        f"target_id={user_id} company={deleted_company!r}"
    )
    await query.message.answer("Регистрация удалена. Статус пользователя в группе не изменен.")
