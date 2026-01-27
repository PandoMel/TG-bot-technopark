"""
Настройка логирования для бота
"""
import logging
from logging.handlers import RotatingFileHandler


def setup_logging():
    """Настраивает логирование: bot.log и KPP.log с ротацией"""
    
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Логгер для основного бота
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    handlerRotateLog = RotatingFileHandler(
        'bot.log',
        maxBytes=15 * 1024 * 1024,  # 15 МБ
        backupCount=50,
        encoding='utf-8'
    )
    handlerRotateLog.setFormatter(
        logging.Formatter('%(asctime)s %(name)s %(message)s', date_format)
    )
    root_logger.addHandler(handlerRotateLog)
    
    # Логгер для пропусков
    ohrana_logger = logging.getLogger('KPP')
    ohrana_logger.setLevel(logging.INFO)
    
    handlerKPPlogs = RotatingFileHandler(
        'KPP.log',
        maxBytes=10 * 1024 * 1024,  # 10 МБ
        backupCount=200,
        encoding='utf-8'
    )
    handlerKPPlogs.setFormatter(
        logging.Formatter('%(asctime)s %(message)s', date_format)
    )
    ohrana_logger.addHandler(handlerKPPlogs)
    
    return root_logger, ohrana_logger


def get_kpp_logger():
    """Возвращает логгер для пропусков"""
    return logging.getLogger('KPP')


def get_root_logger():
    """Возвращает корневой логгер"""
    return logging.getLogger()
