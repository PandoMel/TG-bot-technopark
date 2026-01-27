"""
Настройка логирования для бота
"""
import logging
from logging.handlers import RotatingFileHandler
from config import date_format

handlerRotateLog = RotatingFileHandler(
    'bot.log', 
    maxBytes=15 * 1024 * 1024,
    backupCount=50,
    encoding='utf-8')
handlerRotateLog.setFormatter(logging.Formatter('%(asctime)s %(name)s %(message)s', date_format))

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

handlerKPPlogs = RotatingFileHandler(
    'KPP.log',
    maxBytes=10 * 1024 * 1024,
    backupCount=200,
    encoding='utf-8')

def rotate_logs():
    root_logger.addHandler(handlerRotateLog)

rotate_logs()

ohrana_logger = logging.getLogger('KPP')
ohrana_logger.setLevel(logging.INFO)
ohrana_logger.addHandler(handlerKPPlogs)
handlerKPPlogs.setFormatter(logging.Formatter('%(asctime)s %(message)s', date_format))
