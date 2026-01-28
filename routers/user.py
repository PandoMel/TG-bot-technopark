"""
Роутер для основного флоу: регистрация/заказ пропусков
aiogram 3.14
"""
import asyncio
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from config import bot, CHANNEL_ID, OHRANA_ID, manual_avto, manual_peshkom, error_send_propusk
from keyboards import builder, key_builder, builder2
from database import load_bd, find_in_bd, input_bd, save_bd
from services import check_members, can_send_message
from FSMstates import Form
from logging_module import root_logger, ohrana_logger
from html_export import to_html

router = Router()

@dp.message(Command("start")) # Примечание: dp здесь нет, нужно заменить на router
# В новых роутерах декоратор @router.message, а не @dp.message
# Исправленный код ниже:

@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    load_bd()
    test1 = str(message.from_user.id)
    id_find = find_in_bd(test1)
    root_logger.info(f'id_find: {id_find}')
    check_usr = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=message.from_user.id)
    if (check_usr.status != "left") and (check_usr.status != "kicked"):
        root_logger.info(f'/start: access user: {check_usr.user.username}, status: {check_usr.status}')
        if id_find == "null":
            await message.answer('Необходимо пройти регистрацию. Пожалуйста, поделитесь своим номером телефона...',
                                 reply_markup=key_builder.as_markup(resize_keyboard=True, one_time_keyboard=True))
            await state.set_state(Form.num_phone)
        else:
            await message.answer(f'Ваши данные: {id_find}')
            await state.update_data(company_stat=id_find)
            await message.answer(f"Для оформления пропуска посетителю технопарка нажмите кнопку ↓", reply_markup=builder.as_markup())
    else:
        await message.answer("Отказано. Вы должны состоять в специальной группе для доступа к функциям бота.")
        root_logger.info(f'/start: access denied user: {check_usr.user.username}, status: {check_usr.status}')
        await state.clear()
    
    if (check_usr.status == "creator") or (check_usr.status == 'administrator'):
        await asyncio.sleep(0.3)
        # Импорт adm_button здесь или вверху. Для чистоты лучше импортировать всё вверху.
        from keyboards import adm_button 
        await message.answer('Вы администратор, дополнительные функции по кнопке ↓', reply_markup=adm_button.as_markup())
        root_logger.warning(f'Admin: {check_usr.status}. ID: {message.from_user.id}')

@router.message(lambda message: message.contact is not None, Form.num_phone)
async def get_contact_keyboard(message: types.Message, state: FSMContext):
    phone_number = message.contact.phone_number
    await state.update_data(num_phone=phone_number)
    await message.answer("Введите наименование вашей организации", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Form.company_stat)

@router.message(Form.company_stat)
async def input_company(message: types.Message, state: FSMContext):
     await state.update_data(company_stat=message.text)
     await message.answer('Введите ваши фамилию и инициалы')
     await state.set_state(Form.fio)

@router.message(Form.fio)
async def names(message: types.Message, state: FSMContext):
    await state.update_data(fio=message.text)
    data = await state.get_data()
    get_fio = data.get('fio')
    get_usr_company = data.get('company_stat')
    get_phone = data.get('num_phone')
    input_bd(usr_id=message.from_user.id, company_usr=get_usr_company+", "+get_fio, phone_contact='+'+get_phone)
    save_bd()
    root_logger.warning(f'Input bd.txt id: {message.from_user.id}, {get_usr_company} {get_fio} user: {message.from_user.full_name}, phone: {get_phone}')
    await state.clear()
    await cmd_start(message, state)

@router.message(Command("status"))
async def cmd_answer(message: types.Message, state: FSMContext):
    await check_members(message)

@router.message(Command("help"))
async def cmd_hello(message: Message):
    from config import help_comand
    await message.answer(help_comand)

@router.callback_query(F.data == "Заказать пропуск")
async def send_zakazat_propusk(query: types.CallbackQuery, state: FSMContext):
    await query.answer()
    await query.message.edit_reply_markup()
    load_bd()
    check_usr = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=query.from_user.id)
    if check_usr.status == 'left':
        await state.clear()
        await query.message.answer('Доступ запрещен')
        return ()
    data = await state.get_data()
    if data.get('company_stat') == None:
        load_bd()
        from_state = (find_in_bd(usr_id=str(query.from_user.id)))
        await state.update_data(company_stat=from_state)
    await query.message.answer(text=f"Введите данные посетителя:\nДля пешего: фамилия, имя, отчество \nДля автомобиля: Полный номер ТС")
    root_logger.warning(f'Load bd. id: {query.from_user.id}')
    await state.set_state(Form.sms)

@router.message(Form.sms)
async def capture_sms(message: Message, state: FSMContext):
    check_sms = message.text
    await state.update_data(sms=check_sms)
    keyboard_list = [
        [types.InlineKeyboardButton(text="✅Подтвердить", callback_data="yes_send_button")],
        [types.InlineKeyboardButton(text="❌Отменить", callback_data="cancel")]]
    key_cnf = InlineKeyboardBuilder(keyboard_list)
    data = await state.get_data()
    msg_text = (f'Подтвердите данные:\n{data.get("sms")}')
    await message.answer(msg_text, reply_markup=key_cnf.as_markup())

@router.callback_query(F.data == "yes_send_button")
async def callb_msg(query: types.CallbackQuery, state: FSMContext):
    await query.answer()
    await bot.edit_message_text(text='Заявка в обработке...', chat_id=query.message.chat.id, message_id=query.message.message_id)
    usr = query.from_user
    data = await state.get_data()
    usr_comp = data.get('company_stat')
    sms = data.get("sms")
    usr_fname = usr.first_name or ''
    usr_lname = usr.last_name or ''
    usr_name = f"@{usr.username}" if usr.username else ''

    if sms == None:
        await query.message.answer('Ошибка, данные сообщения утеряны. Пожалуйста, начните с начала командой: /start')
        await state.clear()
        return

    sms_processed = sms.replace('\n', ', ')
    msg_text = (f'От: {usr_name} {usr_fname} {usr_lname} {usr_comp}\nДля: {sms_processed}')

    if not await can_send_message(sms_processed, query.from_user.id):
        await query.message.answer(f"Пропуск с этими данными уже был оформлен одним из пользователей системы. Ваше сообщение не доставлено. \nИспользуйте /start")
        root_logger.info(f'Пропуск с этими данными уже был оформлен одним из пользователей системы. Data: {msg_text}')
        return

    try:
        await bot.send_message(chat_id=OHRANA_ID, text=msg_text)
    except:
        await query.message.answer(error_send_propusk)
        return

    await asyncio.sleep(1.1)
    await bot.edit_message_text(text=f"Заявка передана на охрану с данными:\n{sms}",
                                chat_id=query.message.chat.id,
                                message_id=query.message.message_id,
                                reply_markup=builder2.as_markup())
    dt = str(usr_comp) + " ДЛЯ: " + str(sms_processed)
    to_html(dt)
    root_logger.warning(f'Message in OHRANA. ID: {usr.id}, user: {usr.full_name}')
    root_logger.info(msg_text)
    ohrana_logger.info(f'От {usr_comp} Для: {sms_processed.replace('\n', '. ')}')
    await state.clear()

@router.callback_query(F.data == "cancel")
async def cancel_data(query: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await query.answer()
    await query.message.delete_reply_markup()
    await query.message.answer(f'Отменено.\nИспользуйте команду: /start')

@router.callback_query(F.data == 'man_avto')
async def manual(query: types.CallbackQuery):
    await query.answer()
    await query.message.delete_reply_markup()
    await query.message.answer(text=manual_avto, reply_markup=builder.as_markup())

@router.callback_query(F.data == 'man_pesh')
async def manual(query: types.CallbackQuery):
    await query.answer()
    await query.message.delete_reply_markup()
    await query.message.answer(text=manual_peshkom, reply_markup=builder.as_markup())

@router.message(F.text)
async def lovim_text(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer('Ошибка. Отправляйте данные согласно диалогу.\nИспользуйте команду: /start')
