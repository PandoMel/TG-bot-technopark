"""
Роутер для админ-панели
aiogram 3.14
"""
import asyncio
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from config import bot, CHANNEL_ID
from keyboards import adm_keys, get_delete_button
from database import load_bd, find_by_name, id, company, phone, del_bd, save_bd, find_return_ID
from FSMstates import Form
from logging_module import root_logger
from services import tail, tail_len

router = Router()

@router.callback_query(F.data == 'admins')
async def for_adm(query: types.CallbackQuery):
    await query.message.answer('Выберите необходимое действие из меню', reply_markup=adm_keys.as_markup())

@router.callback_query(F.data == 'edit_bd')
async def cat_edit_bd(query: types.CallbackQuery, state: FSMContext):
    await query.message.answer('Введите номер элемента из БД для редактирования(можно получить по кнопке "Поиск пользователя")')
    await state.set_state(Form.edit_db_old)

@router.message(Form.edit_db_old)
async def edit_bd_old_handler(message: types.Message, state: FSMContext):
    load_bd()
    await state.update_data(edit_bd_old=message.text)
    try:
        idx = int(message.text)
        await message.answer(f'Выбран элемент:\n{id[idx]} {company[idx]} {phone[idx]}')
        await message.answer('Введите на что поменять? В формате: "компания, ФИО"')
        await state.set_state(Form.edit_db_new)
    except:
        await message.answer('Ошибка индекса')

@router.message(Form.edit_db_new)
async def edit_bd_new_handler(message: types.Message, state: FSMContext):
    load_bd()
    data = await state.get_data()
    a = int(data.get('edit_bd_old'))
    b = message.text
    company[a] = str(b)
    await message.answer(f'Обновлено: {id[a]} {company[a]} {phone[a]}')
    save_bd()

@router.callback_query(F.data == 'reg')
async def reg(query: types.CallbackQuery, state: FSMContext):
    await query.message.answer('Для вашего ID. Введите организацию(2-ой шаг регистации). Функция может давать сбои')
    await state.set_state(Form.company_stat)

@router.callback_query(F.data == 'cat_bd')
async def catbd(query: types.CallbackQuery):
    try:
        with open('bd.txt', 'r', encoding='utf-8') as file:
            file_rd = file.read()
            chunk_size = 4096
            chunks = [file_rd[i:i + chunk_size] for i in range(0, len(file_rd), chunk_size)]
            for chunk in chunks:
                await query.message.answer(chunk)
                await asyncio.sleep(0.3)
    except FileNotFoundError:
        await query.message.answer("Файл БД не найден")

@router.callback_query(F.data == 'find_bd')
async def amd_key_find(query: types.CallbackQuery, state: FSMContext):
    await query.message.answer(f'Функция поиска пользователя в базе данных. Введите название компании или фамилию пользователя, или ID.')
    await state.set_state(Form.adm_find)

@router.message(Form.adm_find)
async def func_find(message: types.Message, state: FSMContext):
    await state.update_data(adm_keys=message.text)
    find = find_by_name(message.text)
    if find == -2:
        await message.answer("Введите более точно, есть несколько совпадений в базе")
    elif find == -1:
        await message.answer("Не найдено совпадений в базе")
    elif find >= 0:
        user_info = f'Номер в базе: {str(find)}\n{id[find]} {company[find]} {phone[find]}\n'
        await message.answer(f'{user_info}\n!!! Если Вы хотите заблокировать этого пользователя, то нажмите кнопку ↓',
                             reply_markup=get_delete_button(id[find]))

@router.callback_query(F.data == 'del_bd')
async def func_del_bd(query: types.CallbackQuery, state: FSMContext):
    await query.message.answer('Введите номер элемента из базы данных(можно получить по кнопке "Поиск пользователя")')
    await state.set_state(Form.del_elm)

@router.message(Form.del_elm)
async def del_elm(message: types.Message, state: FSMContext):
    load_bd()
    elm = int(message.text)
    if (elm > len(id)) or (elm < 0):
        await message.answer(f'Некорректное значение')
    else:
        await message.answer(f'Удалена запись #{elm}\n{id[elm]} {company[elm]}\n')
        root_logger.warning(f'Удалена запись #{elm}\n{id[elm]} {company[elm]}\n')
        del_bd(elm)

@router.callback_query(lambda c: c.data.startswith('del_users_from_group_'))
async def delete_user_handler(query: types.CallbackQuery):
    user_id = int(query.data.split('_')[-1])
    try:
        await bot.ban_chat_member(CHANNEL_ID, user_id)
        await bot.unban_chat_member(CHANNEL_ID, user_id)
        index = find_return_ID(str(user_id))
        if index == "null" or index == -1:
            await query.message.answer(f'Пользователь с ID {user_id} не найден в базе данных(в кэше).')
            return
        del_bd(int(index))
        save_bd()
        await query.message.answer(f"Удалён пользователь с ID: {user_id}")
        root_logger.warning(f"Удалён пользователь с ID: {user_id}")
    except TelegramBadRequest as e:
        await query.message.answer(f'Ошибка при удалении пользователя из группы: {e}')

@router.callback_query(F.data == 'cat_log')
async def cat_logs(query: types.CallbackQuery):
    with open('bot.log', 'rb') as f:
        catLOG = str(tail(f=f))
        await query.message.answer(catLOG)

@router.callback_query(F.data == 'cat_KPP')
async def cat_kpp(query: types.CallbackQuery):
    with open('KPP.log', 'r', encoding='utf-8') as file:
        catKPP = str(tail_len(f=file))
        await query.message.answer(catKPP)

@router.callback_query(F.data == 'phone')
async def cat_phone(query: types.CallbackQuery):
    try:
        with open('phone.txt', 'r', encoding='utf-8') as file:
            file_rd = file.read()
            chunk_size = 4096
            chunks = [file_rd[i:i + chunk_size] for i in range(0, len(file_rd), chunk_size)]
            for chunk in chunks:
                await query.message.answer(chunk)
                await asyncio.sleep(0.3)
    except FileNotFoundError:
        await query.message.answer("Файл phone.txt не найден")

@router.callback_query(F.data == 'load_bd')
async def run_load_bd(query: types.CallbackQuery):
    id.clear()
    company.clear()
    phone.clear()
    company.append("None")
    id.append("None")
    phone.append("None")
    load_bd()
    await query.message.answer('БД перезагружена.')
