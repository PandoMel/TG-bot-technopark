"""
FSM состояния для aiogram 3.14
"""
from aiogram.fsm.state import StatesGroup, State

class Form(StatesGroup):
    fio = State()
    company_stat = State()
    sms = State()
    status = State()
    adm_find = State()
    edit_db_new = State()
    edit_db_old = State()
    del_elm = State()
    adm_user_profile = State()
    adm_company_list = State()
    num_phone = State()
    repair_category = State()
    repair_address = State()
    repair_description = State()
    repair_media = State()
    repair_confirm = State()
