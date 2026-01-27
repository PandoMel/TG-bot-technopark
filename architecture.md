# Architecture Documentation

## Project Structure Overview

```
project/
├── bot.py                 # Entry point: Bot initialization, dispatcher setup, polling
├── config.py              # Single configuration file: tokens, IDs, settings, texts
├── FSMstates.py          # FSM State definitions for registration and admin workflows
├── keyboards.py          # Unified keyboard builders (inline/reply) with best practices
├── database.py           # BD.txt operations: load, save, search, insert, delete
├── services.py           # Business logic: validators, access control, messaging, logs
├── html_export.py        # HTML file management for pass records
├── logging.py            # Logging setup: rotating handlers, formatters
├── routers/
│   ├── __init__.py
│   ├── user.py           # User workflows: /start, registration, pass ordering
│   ├── admin.py          # Admin functions: search, edit, delete, logs
│   └── events.py         # System events: user join/leave notifications
├── README.md
├── architecture.md       # This file
└── agent.md             # Development guidelines
```

## Module Responsibilities

### Core Modules

**config.py**
- Centralized configuration: bot token, chat IDs, file paths
- Logging parameters: rotating handler settings, formatters
- Service settings: time windows, chunk sizes
- Text messages: help texts, instructions, error messages

**FSMstates.py**
- FSM StateGroup for user registration flow
- FSM StateGroup for admin management workflows
- Minimal, focused state definitions

**keyboards.py**
- Inline keyboard builders (with `get_*` prefix)
- Reply keyboard builders
- Best practice: consistent naming, type hints, descriptive docstrings
- No complex logic, only keyboard assembly

### Router Modules (routers/)

**user.py**
- `/start` command: access check, registration, menu
- `/status`, `/help` commands
- Registration flow: phone → company → FIO
- Pass ordering: details input → confirmation → sending
- Instructions display (vehicle, pedestrian)

**admin.py**
- Admin menu with database operations
- Search, edit, delete users in BD
- Database file display
- Log viewers (KPP, bot logs)
- Phone contacts display
- Force reload database

**events.py**
- Chat member join/leave events
- Notifications to admin IDs

### Service Modules

**database.py**
- In-memory storage (id_list, company_list, phone_list)
- `load_bd()`: read BD.txt into memory
- `save_bd()`: write memory to BD.txt
- `find_by_id()`, `find_by_name()`: search operations
- `insert_record()`, `edit_record()`, `delete_record()`: CRUD
- `get_all_companies()`: list for matching validation

**services.py**
- **Anti-Duplicate Block**: `can_send_message()`, `reset_sent_messages()`
- **Validators Block**: `validate_not_empty()`, `validate_phone()`, `validate_vehicle_plate()`, company matching
- **Access Control Block**: `check_user_access()` - verify user in CHANNEL_ID
- **Messaging Block**: `send_pass_request_to_ohrana()`, `send_text_chunks()`
- **Log Reading Block**: `read_log_tail()` - fetch last N lines from logs

**html_export.py**
- `append_pass_to_html()`: add pass record, handle date changes
- `_create_new_html_file()`: initialize new HTML file

**logging.py**
- `setup_logging()`: configures root logger and KPP logger
- Rotating file handlers for bot.log and KPP.log
- Reads settings from config.py

### Entry Point

**bot.py**
- Initializes Bot and Dispatcher
- Includes all routers (user, admin, events)
- Sets bot commands
- Starts polling loop
- Creates background tasks (anti-duplicate reset)

## Data Flow

### Registration Flow
```
/start → Database check
  ├─ User found → Show company + order button
  └─ User not found → Request phone
       → Phone shared → Request company
            → Company input (with matching)
                 → FIO input
                      → Save to database + Restart
```

### Pass Ordering Flow
```
Order button → Input pass details (vehicle/visitor)
  → Confirmation → Duplicate check
       ├─ Duplicate → Reject with message
       └─ Unique → Send to OHRANA_ID
            → Log to HTML
            → Log to KPP logger
            → Show success + instructions
```

### Admin Search Flow
```
Admin search → Query database
  ├─ No matches → Show "not found"
  ├─ Multiple matches → Ask to be more specific
  └─ Single match → Show user info + delete button (optional)
```

## Key Design Decisions

1. **Single Config File**: All settings centralized for easy management and environment variable support
2. **Best Practice Keyboards**: Using `builder.button()` and `builder.adjust()` for consistent, readable keyboard definitions
3. **Service Separation**: Business logic separated from Telegram handlers for testability
4. **Database Abstraction**: BD.txt operations encapsulated in `database.py` module
5. **Multi-Block Services**: `services.py` organized into logical blocks (anti-duplicate, validators, access, messaging, logs)
6. **Router Organization**: Clear separation of concerns (user, admin, events)
7. **Logging Strategy**: Dual loggers (root for general, KPP for pass records) with rotating handlers

## Future Improvements

- [ ] Add asyncio.Lock() to database write operations for thread-safety
- [ ] Implement cache for `load_bd()` with cache invalidation
- [ ] Add type hints to database module (using dataclasses)
- [ ] Migrate BD.txt to SQLite for better performance
- [ ] Add unit tests for validators and database functions
- [ ] Implement state persistence (Redis) for FSM
- [ ] Add request rate limiting per user
- [ ] Enhanced error handling with custom exceptions
