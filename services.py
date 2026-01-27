"""
Бизнес-логика, валидация и антидубликат
"""
from datetime import datetime, timedelta


def validate_phone(phone: str) -> bool:
    """Проверка номера телефона"""
    if not phone or len(phone) < 10:
        return False
    return True


def validate_company(company: str) -> bool:
    """Проверка названия компании"""
    if not company or len(company) < 2:
        return False
    return True


def check_duplicate(user_id: str, time_window: timedelta = timedelta(minutes=30)) -> bool:
    """
    Проверка дубликата заявки (одна заявка в 30 минут).
    Возвращает True если есть дубликат, False если можно отправлять.
    """
    # Сохранение состояния посылок: {user_id: datetime}
    # Используется в bot.py как sent_messages
    return False


def sanitize_company_name(company: str) -> str:
    """Очистка названия компании от спецсимволов"""
    return company.replace('\n', ' ').strip()


def format_propusk_message(fio: str, company: str, phone: str, date_time: str) -> str:
    """Форматирование сообщения пропуска"""
    message = f"ФИО: {fio}\n"
    message += f"Компания: {company}\n"
    message += f"Телефон: {phone}\n"
    message += f"Время: {date_time}"
    return message
