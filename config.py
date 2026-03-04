
from datetime import timedelta
from pathlib import Path

from aiogram import Bot
from aiogram.types import BotCommand

bot_token = "000000000000:AAE_abc0000000000000000000000000000000"
ADMINS = [0000, 1111]

OHRANA_ID = -100000000000  # Канал куда отправлять заявку пользователя
CHANNEL_ID = -100000000000  # Группа-база данных, откуда бот будет проверять наличие доступа пользователя к своим функциям
AXO_ID = -100000000000  # Канал/группа для заявок на ремонт

REPAIR_REQUESTS_ENABLED = True
REPAIR_SEND_ENABLED = True

# ===== File Paths =====
BASE_DIR = Path(__file__).parent
PATH_BD = BASE_DIR / "bd.txt"
PATH_INDEX_HTML = BASE_DIR / "index.html"
PATH_BOT_LOG = BASE_DIR / "bot.log"
PATH_KPP_LOG = BASE_DIR / "KPP.log"
PATH_UK_LOG = BASE_DIR / "UK.log"
PATH_GROUP_MEMBERS = BASE_DIR / "group_members.json"

# ===== Logging Settings =====
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_FORMAT = "%(asctime)s %(name)s %(message)s"
date_format = LOG_DATE_FORMAT

BOT_LOG_MAX_BYTES = 15 * 1024 * 1024  # 15 MB
BOT_LOG_BACKUP_COUNT = 50
KPP_LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
KPP_LOG_BACKUP_COUNT = 200
UK_LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
UK_LOG_BACKUP_COUNT = 200

# ===== Service Settings =====
TIME_WINDOW = timedelta(minutes=30)  # Anti-duplicate check window
CHUNK_SIZE = 4096  # For sending large files in parts
HTML_HEADER_LINES = 6  # Reserved lines in index.html for header

# ===== Command Descriptions =====
BOT_COMMANDS_DESCRIPTIONS = {
    "start": "Запуск",
    "status": "Статус доступа",
    "help": "Помощь",
}

bot_commands = [
    BotCommand(command=command, description=description)
    for command, description in BOT_COMMANDS_DESCRIPTIONS.items()
]

bot = Bot(token=bot_token)

# ===== Text Messages =====
help_comand = (
    "Здравствуйте!\n"
    "Этот бот создан для заказа пропусков на территорию предприятия сотрудниками компаний-резидентов.\n"
    "\n"
    "Чтобы у Вас была возможность заказывать пропуска, необходимо подойти к Коменданту и "
    "после оформления соответствующих разрешений получить доступ к функциям бота.\n"
    "\n"
    "Если у Вас есть технические вопросы либо предложения по улучшению функционала, обратитесь к администраторам"
)

error_send_propusk = (
    "Не удалось отправить сообщение в группу охраны. "
    "Повторите попытку через некоторое время, возможно неисправности в сетях связи. "
    "При повторном возникновении ошибки обратитесь к IT службе.\n"
    "\nВернуться в начало: /start"
)

manual_avto = (
    "Припарковать автомобиль возле КПП с правой стороны по ходу Вашего движения (не мешая проезду).\n"
    "Зайти на КПП, сообщить охраннику в какую организацию направляетесь а также номер транспортного средства. "
    "После проверки документов на транспортное средство выдадут временный пропуск (пластиковую карту), "
    "ее приложить на въезде к считывателю и проехать.\n"
    "После посещения необходимо вернуть временный пропуск на КПП охраннику."
)

manual_peshkom = (
    "Зайти на КПП, сообщить охраннику свою фамилию и организацию в которую направляетесь.\n"
    "После предоставления документов подтверждающих Вашу личность (паспорт, водительское удостоверение и т.д.) "
    "получить временный пропуск (пластиковую карту) и пройти через турникет.\n"
    "После посещения необходимо вернуть временный пропуск на КПП охраннику."
)
