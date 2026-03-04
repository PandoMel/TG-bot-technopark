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
    builder.add(types.InlineKeyboardButton( #builder.row для расположения в 2 строки кнопок, либо builder.add для одной строки
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

admKeyList = [
    [types.InlineKeyboardButton(text='Поиск данных пользователя', callback_data='find_bd')],
    [types.InlineKeyboardButton(text='Профиль пользователя по ID', callback_data='user_profile')],
    [types.InlineKeyboardButton(text='Просмотреть список компании', callback_data='company_list')],
    [types.InlineKeyboardButton(text='Показать незарегистрированных в группе', callback_data='unregistered_members')],
    [types.InlineKeyboardButton(text='Редактировать пользователя в БД', callback_data='edit_bd')],
    [types.InlineKeyboardButton(text='Удалить регистрацию пользователя в БД', callback_data='del_bd')],
    [types.InlineKeyboardButton(text='Загрузить БД из файла в память', callback_data='load_bd')],
    [types.InlineKeyboardButton(text='Показать(файл) БД', callback_data='cat_bd')],
    [types.InlineKeyboardButton(text='Просмотр посл. заявок пропусков', callback_data='cat_KPP')],
    [types.InlineKeyboardButton(text='Показать логи бота', callback_data='cat_log')],
    [types.InlineKeyboardButton(text='Получить контакт пользователя', callback_data='phone')]
]
adm_keys = InlineKeyboardBuilder(admKeyList)

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
