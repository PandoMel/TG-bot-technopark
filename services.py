"""
Бизнес-логика, валидация и антидубликат
"""
import asyncio
from datetime import datetime
from aiogram import types
from config import bot, CHANNEL_ID, TIME_WINDOW
from database import sent_messages
from log_config import root_logger

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
