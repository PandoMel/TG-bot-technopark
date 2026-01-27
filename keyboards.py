"""
Кнопки (Inline + Reply) для aiogram 3.14
"""
from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

# Пользовательские кнопки
builder = InlineKeyboardBuilder()
builder.add(types.InlineKeyboardButton(
    text="Заказать гостевой пропуск",
    callback_data="Заказать пропуск"))

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
