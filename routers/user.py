"""
Роутер для основного флоу: регистрация/заказ пропусков
aiogram 3.14
"""
import asyncio
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import (
    AXO_ID,
    CHANNEL_ID,
    OHRANA_ID,
    REPAIR_REQUESTS_ENABLED,
    REPAIR_SEND_ENABLED,
    bot,
    error_send_propusk,
    manual_avto,
    manual_peshkom,
)
from keyboards import (
    adm_button,
    builder,
    builder2,
    get_repair_categories_keyboard,
    get_repair_confirm_keyboard,
    get_repair_skip_media_keyboard,
    get_repair_status_keyboard,
    key_builder,
)
from database import load_bd, find_in_bd, input_bd, save_bd
from services import check_members, can_send_message
from FSMstates import Form
from logging_module import root_logger, ohrana_logger, uk_logger
from html_export import to_html

router = Router()

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
    ohrana_logger.info(f"От {usr_comp} Для: {sms_processed.replace('\n', '. ')}")
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

REPAIR_CATEGORY_LABELS = {
    "repair_cat_lift": "Лифт",
    "repair_cat_light": "Освещение",
    "repair_cat_water": "Вода/Отопление",
    "repair_cat_other": "Другое",
}
#убрать отображение данных(от кого) для пользователя, но отправлять полные данные в греппу AXO_ID
def build_repair_message(data: dict, user: types.User) -> str:
    username = f"@{user.username}" if user.username else "не указан"
    return (
        "Заявка на ремонт\n"
        f"Категория: {data.get('repair_category')}\n"
        f"Адрес: {data.get('repair_address')}\n"
        f"Описание: {data.get('repair_description')}\n"
        f"От: {username} ({user.full_name}), ID: {user.id}"
    )

@router.callback_query(F.data == "repair_request")
async def start_repair_request(query: types.CallbackQuery, state: FSMContext):
    await query.answer()
    if not REPAIR_REQUESTS_ENABLED:
        await query.message.answer("Функция заявок на ремонт временно недоступна.")
        return
    await state.clear()
    await query.message.answer(
        "Выберите категорию заявки:",
        reply_markup=get_repair_categories_keyboard()
    )
    await state.set_state(Form.repair_category)

@router.callback_query(F.data.in_(REPAIR_CATEGORY_LABELS.keys()))
async def select_repair_category(query: types.CallbackQuery, state: FSMContext):
    await query.answer()
    category = REPAIR_CATEGORY_LABELS.get(query.data)
    await state.update_data(repair_category=category)
    await query.message.answer("Укажите адрес (этаж, офис).")
    await state.set_state(Form.repair_address)

@router.message(Form.repair_address)
async def input_repair_address(message: Message, state: FSMContext):
    await state.update_data(repair_address=message.text)
    await message.answer("Опишите проблему.")
    await state.set_state(Form.repair_description)

@router.message(Form.repair_description)
async def input_repair_description(message: Message, state: FSMContext):
    await state.update_data(repair_description=message.text)
    await message.answer(
        "Если есть фото или видео, отправьте их. Если нет — нажмите «Пропустить».",
        reply_markup=get_repair_skip_media_keyboard()
    )
    await state.set_state(Form.repair_media)

@router.callback_query(F.data == "repair_skip_media")
async def skip_repair_media(query: types.CallbackQuery, state: FSMContext):
    await query.answer()
    data = await state.get_data()
    preview_text = build_repair_message(data, query.from_user)
    await query.message.answer(
        f"Проверьте данные заявки:\n\n{preview_text}",
        reply_markup=get_repair_confirm_keyboard()
    )
    await state.set_state(Form.repair_confirm)

@router.message(Form.repair_media)
async def capture_repair_media(message: Message, state: FSMContext):
    media_type = None
    media_id = None
    if message.photo:
        media_type = "photo"
        media_id = message.photo[-1].file_id
    elif message.video:
        media_type = "video"
        media_id = message.video.file_id

    if not media_type or not media_id:
        await message.answer("Пожалуйста, отправьте фото или видео, либо нажмите «Пропустить».")
        return

    await state.update_data(repair_media_type=media_type, repair_media_id=media_id)
    data = await state.get_data()
    preview_text = build_repair_message(data, message.from_user)
    await message.answer(
        f"Проверьте данные заявки:\n\n{preview_text}",
        reply_markup=get_repair_confirm_keyboard()
    )
    await state.set_state(Form.repair_confirm)

@router.callback_query(F.data == "repair_confirm_send")
async def send_repair_request(query: types.CallbackQuery, state: FSMContext):
    await query.answer()
    if not REPAIR_SEND_ENABLED:
        await query.message.answer("Отправка заявок временно отключена.")
        await state.clear()
        return
    data = await state.get_data()
    #check data !=None
    if not data or not data.get("repair_description"):
        await query.message.answer("Ошибка: данные заявки утеряны (время сессии истекло). Пожалуйста, заполните заявку заново.")
        await state.clear()
        return
    
    message_text = build_repair_message(data, query.from_user)
    media_type = data.get("repair_media_type")
    media_id = data.get("repair_media_id")
    try:
        if media_type == "photo":
            await bot.send_photo(
                chat_id=AXO_ID,
                photo=media_id,
                caption=message_text,
                reply_markup=get_repair_status_keyboard()
            )
        elif media_type == "video":
            await bot.send_video(
                chat_id=AXO_ID,
                video=media_id,
                caption=message_text,
                reply_markup=get_repair_status_keyboard()
            )
        else:
            await bot.send_message(
                chat_id=AXO_ID,
                text=message_text,
                reply_markup=get_repair_status_keyboard()
            )
    except Exception as exc:
        root_logger.error(f"Ошибка отправки заявки на ремонт: {exc}")
        await query.message.answer("Не удалось отправить заявку. Повторите попытку позже.")
        return

    uk_logger.info(message_text)
    await query.message.answer("Заявка отправлена. Спасибо!")
    await state.clear()

@router.callback_query(F.data == "repair_confirm_cancel")
async def cancel_repair_request(query: types.CallbackQuery, state: FSMContext):
    await query.answer()
    await state.clear()
    await query.message.answer("Заявка отменена.")

@router.message(F.text)
async def lovim_text(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer('Ошибка. Отправляйте данные согласно диалогу.\nИспользуйте команду: /start')
