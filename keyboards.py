"""
Кнопки (Inline + Reply) для aiogram 3.14
"""
from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from config import REPAIR_REQUESTS_ENABLED, REPAIR_SEND_ENABLED

# Пользовательские кнопки
builder = InlineKeyboardBuilder()
builder.add(types.InlineKeyboardButton(
    text="🎫 Заказ пропуска",
    callback_data="Заказать пропуск"))
if REPAIR_REQUESTS_ENABLED and REPAIR_SEND_ENABLED:
    builder.add(types.InlineKeyboardButton(
        text="🛠 Заявка на ремонт",
        callback_data="repair_request"))

keys_after_send = [
    [types.InlineKeyboardButton(text='Инструкция посетителю(авто)', callback_data='man_avto')],
    [types.InlineKeyboardButton(text='Инструкция посетителю(пеший)', callback_data='man_pesh')],
    [types.InlineKeyboardButton(text="Создать новый пропуск", callback_data="Заказать пропуск")]
]
builder2 = InlineKeyboardBuilder(keys_after_send)

key_builder = ReplyKeyboardBuilder()
key_builder.add(types.KeyboardButton(text="Отправить номер телефона", request_contact=True))

# Админские кнопки
adm_button = InlineKeyboardBuilder()
adm_button.add(types.InlineKeyboardButton(
    text="Администраторское меню",
    callback_data="admins"))


def get_admin_main_keyboard():
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(
        text="👤 Действия с пользователями",
        callback_data="adm_users_menu",
    ))
    kb.row(types.InlineKeyboardButton(
        text="🏢 Компании",
        callback_data="adm_companies_menu",
    ))
    kb.row(types.InlineKeyboardButton(
        text="🗄 База данных",
        callback_data="adm_database_menu",
    ))
    kb.row(types.InlineKeyboardButton(
        text="🛠 Сервисные функции",
        callback_data="adm_service_menu",
    ))
    return kb


def get_admin_service_keyboard():
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(
        text="Последние заявки на пропуск",
        callback_data="cat_KPP",
    ))
    kb.row(types.InlineKeyboardButton(
        text="Логи бота",
        callback_data="cat_log",
    ))
    kb.row(types.InlineKeyboardButton(
        text="Контакты пользователей",
        callback_data="phone",
    ))
    kb.row(types.InlineKeyboardButton(
        text="⬅️ Назад",
        callback_data="adm_back_main",
    ))
    return kb


def get_admin_database_keyboard():
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(
        text="Показать файл БД",
        callback_data="cat_bd",
    ))
    kb.row(types.InlineKeyboardButton(
        text="Перезагрузить БД из файла",
        callback_data="load_bd",
    ))
    kb.row(types.InlineKeyboardButton(
        text="⬅️ Назад",
        callback_data="adm_back_main",
    ))
    return kb


def get_admin_companies_keyboard():
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(
        text="Сотрудники компании",
        callback_data="company_list",
    ))
    kb.row(types.InlineKeyboardButton(
        text="⬅️ Назад",
        callback_data="adm_back_main",
    ))
    return kb


# Совместимость со старым обработчиком routers/admin.py.
adm_keys = get_admin_main_keyboard()


def get_delete_button(user_id: int):
    kb = InlineKeyboardBuilder()
    kb.add(types.InlineKeyboardButton(
        text=f'!!! Удалить из группы пользователя {user_id}',
        callback_data=f'del_users_from_group_{user_id}'
    ))
    return kb.as_markup()


def get_repair_categories_keyboard():
    kb = InlineKeyboardBuilder()
    kb.add(types.InlineKeyboardButton(text="🚪 Лифт", callback_data="repair_cat_lift"))
    kb.add(types.InlineKeyboardButton(text="💡 Освещение", callback_data="repair_cat_light"))
    kb.add(types.InlineKeyboardButton(text="🚿 Вода/Отопление", callback_data="repair_cat_water"))
    kb.add(types.InlineKeyboardButton(text="🧹 Другое", callback_data="repair_cat_other"))
    kb.add(types.InlineKeyboardButton(text="❌ Отмена", callback_data="repair_cancel"))
    kb.adjust(1)
    return kb.as_markup()


def get_repair_skip_media_keyboard():
    kb = InlineKeyboardBuilder()
    kb.add(types.InlineKeyboardButton(text="Пропустить", callback_data="repair_skip_media"))
    return kb.as_markup()


def get_repair_confirm_keyboard():
    kb = InlineKeyboardBuilder()
    kb.add(types.InlineKeyboardButton(text="Отправить", callback_data="repair_confirm_send"))
    kb.add(types.InlineKeyboardButton(text="Отмена", callback_data="repair_confirm_cancel"))
    kb.adjust(2)
    return kb.as_markup()


def get_repair_status_keyboard():
    kb = InlineKeyboardBuilder()
    kb.add(types.InlineKeyboardButton(text="Заявка отработана", callback_data="repair_done"))
    return kb.as_markup()
