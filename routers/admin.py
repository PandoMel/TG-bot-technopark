"""
Роутер для админ-панели
aiogram 3.14
"""
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.filters import Command

from config import ADMINS
from FSMstates import AdminStates
from keyboards import get_admin_menu_keyboard
from database import find_in_bd, find_by_name, find_return_ID, del_bd, load_bd
from logging_module import get_root_logger, get_kpp_logger

router = Router()
root_logger = get_root_logger()
ohrana_logger = get_kpp_logger()


def is_admin(user_id: int) -> bool:
    """Проверка прав администратора"""
    return user_id in ADMINS


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Открытие админ-панели"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещен. Это команда только для администраторов.")
        return
    
    adm_keys = get_admin_menu_keyboard()
    await message.answer(
        "🔧 Администраторское меню:",
        reply_markup=adm_keys.as_markup()
    )


@router.callback_query(F.data == "admins")
async def admin_menu(callback_query: types.CallbackQuery):
    """Админ меню по кнопке"""
    if not is_admin(callback_query.from_user.id):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    adm_keys = get_admin_menu_keyboard()
    await callback_query.message.answer(
        "🔧 Администраторское меню:",
        reply_markup=adm_keys.as_markup()
    )
    await callback_query.answer()


@router.callback_query(F.data == "find_bd")
async def find_user_handler(callback_query: types.CallbackQuery, state: FSMContext):
    """Поиск пользователя в БД"""
    if not is_admin(callback_query.from_user.id):
        return
    
    await callback_query.message.answer("Введите ID или название компании для поиска:")
    await state.set_state(AdminStates.waiting_for_search_query)
    await callback_query.answer()


@router.message(AdminStates.waiting_for_search_query)
async def process_search(message: Message, state: FSMContext):
    """Обработка поиска"""
    query = message.text.strip()
    
    # Пытаемся найти по ID
    company = find_in_bd(query)
    
    if company == "null":
        # Пытаемся найти по названию
        result = find_by_name(query)
        if result == -1:
            await message.answer("❌ Пользователь не найден.")
        elif result == -2:
            await message.answer("⚠️ Найдено несколько результатов. Уточните поиск.")
        else:
            await message.answer(f"✅ Найдено: {company}")
    else:
        await message.answer(f"✅ Найдено: {company}")
    
    await state.clear()


@router.callback_query(F.data == "load_bd")
async def load_database(callback_query: types.CallbackQuery):
    """Загрузить БД из файла"""
    if not is_admin(callback_query.from_user.id):
        return
    
    try:
        load_bd()
        await callback_query.message.answer("✅ БД загружена из файла.")
    except Exception as e:
        await callback_query.message.answer(f"❌ Ошибка: {str(e)}")
    
    await callback_query.answer()


@router.callback_query(F.data == "cat_bd")
async def show_database(callback_query: types.CallbackQuery):
    """Показать БД (отправить файл)"""
    if not is_admin(callback_query.from_user.id):
        return
    
    try:
        with open('bd.txt', 'rb') as f:
            await callback_query.message.answer_document(f)
    except Exception as e:
        await callback_query.message.answer(f"❌ Ошибка: {str(e)}")
    
    await callback_query.answer()


@router.callback_query(F.data == "cat_KPP")
async def show_kpp_logs(callback_query: types.CallbackQuery):
    """Показать последние заявки пропусков"""
    if not is_admin(callback_query.from_user.id):
        return
    
    try:
        with open('KPP.log', 'rb') as f:
            await callback_query.message.answer_document(f)
    except Exception as e:
        await callback_query.message.answer(f"❌ Ошибка: {str(e)}")
    
    await callback_query.answer()


@router.callback_query(F.data == "cat_log")
async def show_bot_logs(callback_query: types.CallbackQuery):
    """Показать логи бота"""
    if not is_admin(callback_query.from_user.id):
        return
    
    try:
        with open('bot.log', 'rb') as f:
            await callback_query.message.answer_document(f)
    except Exception as e:
        await callback_query.message.answer(f"❌ Ошибка: {str(e)}")
    
    await callback_query.answer()


@router.callback_query(F.data == "phone")
async def get_user_contact(callback_query: types.CallbackQuery, state: FSMContext):
    """Получить контакт пользователя"""
    if not is_admin(callback_query.from_user.id):
        return
    
    await callback_query.message.answer("Введите ID или название компании:")
    await state.set_state(AdminStates.waiting_for_search_query)
    await callback_query.answer()


@router.callback_query(F.data == "del_bd")
async def delete_user(callback_query: types.CallbackQuery, state: FSMContext):
    """Удалить пользователя из БД"""
    if not is_admin(callback_query.from_user.id):
        return
    
    await callback_query.message.answer("Введите ID пользователя для удаления:")
    await state.set_state(AdminStates.waiting_for_delete_id)
    await callback_query.answer()


@router.message(AdminStates.waiting_for_delete_id)
async def process_delete(message: Message, state: FSMContext):
    """Обработка удаления"""
    user_id = message.text.strip()
    idx = find_return_ID(user_id)
    
    if idx == -1:
        await message.answer("❌ Пользователь не найден.")
    else:
        try:
            del_bd(idx)
            await message.answer("✅ Пользователь удален из БД.")
        except Exception as e:
            await message.answer(f"❌ Ошибка: {str(e)}")
    
    await state.clear()
