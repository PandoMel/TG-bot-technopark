"""
Бизнес-логика, валидация и антидубликат
"""
import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from aiogram import types
from config import bot, CHANNEL_ID, PATH_GROUP_MEMBERS, PATH_KPP_LOG, TIME_WINDOW
from database import sent_messages
from logging_module import root_logger

async def check_members(message: types.Message):
    user_channel = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=message.from_user.id)
    if (user_channel.status != "left") and (user_channel.status != "kicked"):
        await message.answer("Есть разрешение доступа к функционалу бота.")
    else:
        await message.answer(f'Разрешение доступа отсутствует. Обратитесь к Коменданту Технопарка. Статус: {user_channel.status}')
        root_logger.info(f'function check_members run, access denied user {user_channel.user.username}, status: {user_channel.status}')

async def can_send_message(sms_processed: str, user_id: int) -> bool:
    now = datetime.now()
    normalized_text = sms_processed.replace(' ', '').replace('\n', '').lower()
    
    for msg_text in list(sent_messages.keys()):
        sent_messages[msg_text] = [
            (uid, ts) for uid, ts in sent_messages[msg_text]
            if now - ts < TIME_WINDOW
        ]
        if not sent_messages[msg_text]:
            del sent_messages[msg_text]

    if normalized_text in sent_messages:
        root_logger.info(f"Сообщение уже было отправлено: {normalized_text}, использует пользователь ID: {user_id}")
        return False

    sent_messages.setdefault(normalized_text, []).append((user_id, now))
    return True

async def reset_sent_messages():
    while True:
        now = datetime.now()
        next_reset_time = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        wait_time = (next_reset_time - now).total_seconds()
        await asyncio.sleep(wait_time)
        sent_messages.clear()

def tail(f, lines=20):
    total_lines_wanted = lines
    BLOCK_SIZE = 1024
    f.seek(0, 2)
    block_end_byte = f.tell()
    lines_to_go = total_lines_wanted
    block_number = -1
    blocks = []
    while lines_to_go > 0 and block_end_byte > 0:
        if (block_end_byte - BLOCK_SIZE > 0):
            f.seek(block_number*BLOCK_SIZE, 2)
            blocks.append(f.read(BLOCK_SIZE))
        else:
            f.seek(0,0)
            blocks.append(f.read(block_end_byte))
        lines_found = blocks[-1].count(b'\n')
        lines_to_go -= lines_found
        block_end_byte -= BLOCK_SIZE
        block_number -= 1
    all_read_text = b''.join(reversed(blocks))
    text_out = all_read_text.decode('utf-8')
    return text_out

def tail_len(f, lines=25):
        read = f.readlines()
        full_length = len(read)
        log = (read[full_length - lines:])
        print(''.join(log))
        return str(''.join(log))

def load_group_members() -> dict:
    if not Path(PATH_GROUP_MEMBERS).exists():
        return {}
    try:
        with open(PATH_GROUP_MEMBERS, 'r', encoding='utf-8') as file:
            data = json.load(file)
            if isinstance(data, dict):
                return data
    except (json.JSONDecodeError, OSError) as exc:
        root_logger.warning(f"Ошибка чтения файла участников группы: {exc}")
    return {}

def save_group_members(data: dict) -> None:
    try:
        with open(PATH_GROUP_MEMBERS, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
    except OSError as exc:
        root_logger.warning(f"Ошибка записи файла участников группы: {exc}")

def add_group_member(user: types.User) -> None:
    data = load_group_members()
    data[str(user.id)] = {
        "username": user.username or "",
        "full_name": user.full_name,
        "joined_at": datetime.now().isoformat(timespec='seconds'),
    }
    save_group_members(data)

def remove_group_member(user_id: int) -> None:
    data = load_group_members()
    data.pop(str(user_id), None)
    save_group_members(data)

def get_group_member(user_id: int) -> dict | None:
    data = load_group_members()
    return data.get(str(user_id))

def list_group_members() -> dict:
    return load_group_members()

def get_recent_passes_for_user(user_id: int, limit: int = 5) -> list[str]:
    if not Path(PATH_KPP_LOG).exists():
        return []
    try:
        with open(PATH_KPP_LOG, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    except OSError as exc:
        root_logger.warning(f"Ошибка чтения KPP.log: {exc}")
        return []

    target = f"ID:{user_id}"
    results = []
    for line in reversed(lines):
        if target in line:
            results.append(line.strip())
            if len(results) >= limit:
                break
    return results
