# Agent Development Guidelines

## Code Standards

### Python Version
- **3.13** - Use modern Python features (type hints, f-strings, structural pattern matching)

### Framework
- **aiogram 3.14.0** - Latest stable version for Telegram Bot API

### Type Hints
- Always add type hints to function signatures
- Use `Optional[T]` for nullable values
- Use descriptive return types

**Good:**
```python
async def check_user_access(bot: Bot, user_id: int, chat_id: int) -> tuple[bool, str]:
    """Check if user has access (return access status and reason)"""
    ...
```

**Bad:**
```python
async def check_user_access(bot, user_id, chat_id):
    ...
```

### Docstrings
- All public functions must have docstrings
- Include parameter descriptions and return type
- Use triple quotes (""")

**Good:**
```python
def validate_phone(phone: str) -> Optional[str]:
    """Validate phone number format
    
    Args:
        phone: Phone number string
    
    Returns:
        None if valid, error message otherwise
    """
```

### Naming Conventions

| Type | Convention | Example |
|------|-----------|---------|
| Functions | snake_case | `get_user_by_id()` |
| Constants | UPPER_SNAKE_CASE | `BOT_TOKEN`, `TIME_WINDOW` |
| Classes | PascalCase | `Form` (StatesGroup) |
| Private functions | _leading_underscore | `_normalize_text()` |
| Keyboard getters | `get_*_keyboard()` | `get_order_pass_keyboard()` |

### Import Organization

1. Standard library
2. Third-party (aiogram, etc.)
3. Local modules

```python
import asyncio
from datetime import datetime

from aiogram import Bot

import config
from FSMstates import Form
```

## Module Organization

### services.py Pattern
Organize into clear blocks with comments:

```python
# ===== Block Name =====

def function_1():
    ...

def function_2():
    ...

# ===== Next Block =====
```

### Router Pattern
Each router file should have:
1. Module docstring
2. Logger setup
3. Router initialization
4. Handlers (grouped by feature)

```python
"""Router description"""

import logging_module
from aiogram import Router, types, F

logger = logging.getLogger(__name__)
router = Router()


@router.message(...)
async def handler_name(...):
    """Handler description"""
    ...
```

## Best Practices

### Logging
- Use `logger.info()` for important events
- Use `logger.warning()` for admin actions
- Use `logger.error()` for exceptions

```python
logger.info(f"User registered: ID={user_id}, Company={company}")
logger.warning(f"Admin action: deleted user {user_id}")
logger.error(f"Failed to send message: {e}")
```

### Error Handling
- Always catch specific exceptions
- Log errors with context
- Provide user-friendly messages

**Good:**
```python
try:
    result = await bot.send_message(chat_id, text)
except TelegramBadRequest as e:
    logger.error(f"Message too large for {chat_id}: {e}")
    await message.answer("❌ Сообщение слишком большое")
```

**Bad:**
```python
try:
    result = await bot.send_message(chat_id, text)
except:
    pass
```

### Keyboard Functions
- Always return `InlineKeyboardBuilder` or `ReplyKeyboardBuilder`
- Use `.button()` method for building
- Use `.adjust()` for layout

**Good:**
```python
def get_order_pass_keyboard() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.button(text="Заказать", callback_data="order_pass")
    builder.button(text="Отмена", callback_data="cancel")
    builder.adjust(1)  # One button per row
    return builder
```

### Database Operations
- Always call `database.load_bd()` before reads
- Always call `database.save_bd()` after writes
- Log changes with admin/user context

```python
database.load_bd()
database.insert_record(user_id, company, phone)
database.save_bd()
logger.warning(f"Admin: inserted user {user_id}")
```

### Configuration
- All settings go in `config.py`
- Use `Path` from pathlib for file paths
- Group settings with comments

**Good:**
```python
# ===== Bot Settings =====
BOT_TOKEN = "..."
ADMINS = [123, 456]

# ===== File Paths =====
PATH_BD = BASE_DIR / "bd.txt"
```

## Anti-Patterns to Avoid

❌ **Magic strings/numbers**
```python
with open("bd.txt", "r") as f:  # WRONG
    ...
```

✅ **Use config constants**
```python
with open(config.PATH_BD, "r") as f:  # GOOD
    ...
```

---

❌ **Global state outside services**
```python
sent_messages = {}  # Loose global
```

✅ **Encapsulate in service**
```python
# In services.py
sent_messages = {}

async def can_send_message(...):
    ...
```

---

❌ **Complex logic in handlers**
```python
@router.message(Form.sms)
async def capture(message):
    # 50 lines of validation, formatting, sending...
```

✅ **Delegate to services**
```python
@router.message(Form.sms)
async def capture(message):
    error = services.validate_not_empty(message.text)
    if error:
        await message.answer(error)
        return
    # Send via service
```

## Testing Recommendations

Create unit tests for:
- `validate_*()` functions
- `find_*()` database operations
- `_normalize_*()` helper functions

```bash
# Example test structure
tests/
├── test_services.py
├── test_database.py
└── test_validators.py
```

## Performance Notes

- `database.load_bd()` loads entire file into memory (acceptable for <1000 users)
- Consider caching with cache invalidation for production
- Anti-duplicate dict grows with daily usage (reset at midnight)
- HTML file accumulates records (consider archiving by date)

## Future Refactoring

When ready to scale:
1. Replace BD.txt with SQLite database
2. Add asyncio.Lock() for concurrent writes
3. Migrate FSM state to Redis
4. Add request rate limiting
5. Implement custom exceptions
6. Add comprehensive test suite
