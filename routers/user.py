"""
Роутер для основного флоу: регистрация/заказ пропусков
aiogram 3.14
"""
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import Command

from config import (
    manual_avto, manual_peshkom, help_comand, error_send_propusk, OHRANA_ID
)
from FSMstates import RegistrationStates
from keyboards import (
    get_main_menu_builder, get_keys_after_send, get_phone_request_keyboard
)
from database import find_in_bd, input_bd
from services import validate_phone, validate_company, sanitize_company_name
from html_export import to_html
from logging_module import get_kpp_logger
from datetime import datetime

router = Router()
ohrana_logger = get_kpp_logger()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик /start"""
    builder = get_main_menu_builder()
    await message.answer("Добро пожаловать!", reply_markup=builder.as_markup())


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик /help"""
    await message.answer(help_comand)


@router.message(Command("status"))
async def cmd_status(message: Message):
    """Обработчик /status - проверка доступа"""
    user_id = str(message.from_user.id)
    company = find_in_bd(user_id)

    if company == "null":
        await message.answer("❌ Вы не зарегистрированы. Обратитесь к администратору.")
    else:
        await message.answer(f"✅ Вы зарегистрированы в компании: {company}")


@router.callback_query(F.data == "Заказать пропуск")
async def start_registration(callback_query: types.CallbackQuery, state: FSMContext):
    """Начало заказа пропуска"""
    await callback_query.message.answer("Укажите название вашей компании:")
    await state.set_state(RegistrationStates.waiting_for_company)
    await callback_query.answer()


@router.message(RegistrationStates.waiting_for_company)
async def process_company(message: Message, state: FSMContext):
    """Обработка названия компании"""
    company = sanitize_company_name(message.text)

    if not validate_company(company):
        await message.answer("❌ Некорректное название компании. Попробуйте снова.")
        return

    await state.update_data(company=company)
    await message.answer("Укажите ваше ФИО:")
    await state.set_state(RegistrationStates.waiting_for_name)


@router.message(RegistrationStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    """Обработка ФИО"""
    fio = message.text.strip()

    await state.update_data(fio=fio)
    key_builder = get_phone_request_keyboard()
    await message.answer(
        "Поделитесь номером телефона:",
        reply_markup=key_builder.as_markup()
    )
    await state.set_state(RegistrationStates.waiting_for_phone)


@router.message(RegistrationStates.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext, bot):
    """Обработка номера телефона и отправка пропуска"""

    # Обработка контакта
    if message.contact:
        phone = message.contact.phone_number
    else:
        phone = message.text.strip()

    if not validate_phone(phone):
        await message.answer("❌ Некорректный номер телефона. Попробуйте снова.")
        return

    data = await state.get_data()
    company = data.get('company')
    fio = data.get('fio')
    user_id = str(message.from_user.id)

    # Добавление в БД
    input_bd(user_id, company, phone)

    # Формирование и отправка пропуска
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    propusk_text = f"ФИО: {fio}\nКомпания: {company}\nТелефон: {phone}\nВремя: {timestamp}"

    try:
        await bot.send_message(OHRANA_ID, propusk_text)
        to_html(propusk_text)
        ohrana_logger.info(propusk_text)
    except Exception as e:
        await message.answer(error_send_propusk)
        return

    builder2 = get_keys_after_send()
    await message.answer(
        "✅ Пропуск заказан!",
        reply_markup=builder2.as_markup()
    )
    await message.answer("Выберите инструкцию:", reply_markup=ReplyKeyboardRemove())

    await state.clear()


@router.callback_query(F.data == "man_avto")
async def manual_avto_handler(callback_query: types.CallbackQuery):
    """Инструкция для автомобилей"""
    await callback_query.message.answer(manual_avto)
    await callback_query.answer()


@router.callback_query(F.data == "man_pesh")
async def manual_pesh_handler(callback_query: types.CallbackQuery):
    """Инструкция для пешеходов"""
    await callback_query.message.answer(manual_peshkom)
    await callback_query.answer()
