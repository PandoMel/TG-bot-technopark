"""
Настройка логирования для бота
"""
import logging
from logging.handlers import RotatingFileHandler
from config import (
    BOT_LOG_BACKUP_COUNT,
    BOT_LOG_MAX_BYTES,
    KPP_LOG_BACKUP_COUNT,
    KPP_LOG_MAX_BYTES,
    LOG_DATE_FORMAT,
    LOG_FORMAT,
    PATH_BOT_LOG,
    PATH_KPP_LOG,
    PATH_UK_LOG,
    UK_LOG_BACKUP_COUNT,
    UK_LOG_MAX_BYTES,
)

handlerRotateLog = RotatingFileHandler(
    PATH_BOT_LOG,
    maxBytes=BOT_LOG_MAX_BYTES,
    backupCount=BOT_LOG_BACKUP_COUNT,
    encoding='utf-8')
handlerRotateLog.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

handlerKPPlogs = RotatingFileHandler(
    PATH_KPP_LOG,
    maxBytes=KPP_LOG_MAX_BYTES,
    backupCount=KPP_LOG_BACKUP_COUNT,
    encoding='utf-8')

def rotate_logs():
    root_logger.addHandler(handlerRotateLog)

rotate_logs()

ohrana_logger = logging.getLogger('KPP')
ohrana_logger.setLevel(logging.INFO)
ohrana_logger.addHandler(handlerKPPlogs)
handlerKPPlogs.setFormatter(logging.Formatter('%(asctime)s %(message)s', LOG_DATE_FORMAT))

handlerUKlogs = RotatingFileHandler(
    PATH_UK_LOG,
    maxBytes=UK_LOG_MAX_BYTES,
    backupCount=UK_LOG_BACKUP_COUNT,
    encoding='utf-8'
)
uk_logger = logging.getLogger('UK')
uk_logger.setLevel(logging.INFO)
uk_logger.addHandler(handlerUKlogs)
handlerUKlogs.setFormatter(logging.Formatter('%(asctime)s %(message)s', LOG_DATE_FORMAT))
