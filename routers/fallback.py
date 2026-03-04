from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

router = Router()


@router.message(F.text)
async def lovim_text(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer('Ошибка. Отправляйте данные согласно диалогу.\nИспользуйте команду: /start')


# На случай “битых” callback_data или устаревших кнопок
@router.callback_query()
async def fallback_callback(call: CallbackQuery):

    await call.answer("Кнопка неактуальна или действие недоступно.", show_alert=True)
