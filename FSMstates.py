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
    num_phone = State()
