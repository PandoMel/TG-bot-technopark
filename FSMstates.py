"""
FSM состояния для aiogram 3.14
"""
from aiogram.fsm.state import StatesGroup, State


class RegistrationStates(StatesGroup):
    """Состояния при регистрации/заказе пропуска"""
    waiting_for_company = State()      # waiting_company_stat
    waiting_for_phone = State()        # waiting_sms
    waiting_for_name = State()


class AdminStates(StatesGroup):
    """Состояния для админ-панели"""
    waiting_for_search_query = State()  # adm_find
    waiting_for_delete_id = State()     # adm_del_bd
    waiting_for_edit_old = State()      # edit_db_old
    waiting_for_edit_new = State()      # edit_db_new


class Form(StatesGroup):
    """Полный набор состояний из оригинального кода"""
    # Основной флоу регистрации
    num_phone = State()  # Запрос контакта (1)
    company_stat = State()  # Ввод компании (2)
    fio = State()  # Ввод ФИО (3)
    
    # Админ-панель
    adm_find = State()                  # Поиск в БД
    adm_del_bd = State()                # Удаление из БД
    edit_db_old = State()               # Редактирование - старое значение
    edit_db_new = State()               # Редактирование - новое значение
