# Architecture Documentation

## Project Structure Overview

```
project/
├── bot.py # Entry point: Bot initialization, dispatcher setup, polling
├── config.py # Central configuration: tokens, IDs, text constants, Bot instance
├── FSMstates.py # FSM State definitions for workflows
├── keyboards.py # Unified keyboard builders (inline/reply)
├── database.py # Data Layer: In-memory arrays + file I/O for bd.txt
├── services.py # Business logic: access control, anti-flood, tail readers
├── html_export.py # HTML file management for pass records
├── logging_module.py # Infrastructure: Logging setup (renamed from logging.py)
├── routers/
│ ├── init.py
│ ├── user.py # User workflows: /start, registration, pass ordering
│ ├── admin.py # Admin functions: search, edit, delete, logs
│ └── events.py # System events: user join/leave notifications
├── bd.txt # Flat-file database (ID;Company;Phone)
├── phone.txt # Supplementary contact file
├── README.md
└── architecture.md # This file
```


## Module Responsibilities

### Core Modules

**config.py**
- Initializes the `Bot` instance (to avoid circular imports).
- Stores secrets (Tokens, IDs) and constants (`TIME_WINDOW`).
- Contains static text strings (Help commands, manuals).

**FSMstates.py**
- `Form(StatesGroup)`: Defines all states for user registration (`fio`, `company_stat`) and admin operations (`edit_db`, `adm_find`).

**keyboards.py**
- `builder`: Main inline keyboard for users.
- `key_builder`: Reply keyboard for contact sharing.
- `adm_keys`: Admin menu builder.
- Helper functions like `get_delete_button(user_id)`.

**logging_module.py**
- Configures `RotatingFileHandler` for `bot.log` (general logs).
- Configures `RotatingFileHandler` for `KPP.log` (security/access logs).
- Defines formatters for log entries.

### Router Modules (routers/)

**user.py**
- `/start`: Initializes user session, checks DB presence.
- Registration flow: Contact share → Company name → Name input -> Save to DB.
- Pass ordering (`send_zakazat_propusk`): Inputs pass details -> Validates -> Sends to `OHRANA_ID`.

**admin.py**
- Admin menu handling (`edit_bd`, `load_bd`, `del_bd`).
- Search functionality (`func_find`).
- Log viewing via Telegram (`cat_log`, `cat_KPP`).
- Database manual reloading.

**events.py**
- Monitors `ChatMemberUpdated` events.
- Notifications: Alerts admins when users join/leave the main chat.

### Service Modules

**database.py**
- **State**: Global arrays `id`, `company`, `phone` acting as in-memory cache.
- `load_bd()`: Parses `bd.txt` into arrays.
- `save_bd()`: Serializes arrays back to `bd.txt`.
- `find_in_bd()` / `find_by_name()`: Search logic (exact and partial match).
- `input_bd()` / `del_bd()`: Cache modification methods.

**services.py**
- **Access Control**: `check_members()` checks user status in `CHANNEL_ID`.
- **Anti-Flood**: `can_send_message()` & `reset_sent_messages()` prevents duplicate pass requests within `TIME_WINDOW`.
- **File Utils**: `tail()` and `tail_len()` for reading log files in chunks for Telegram.

**html_export.py**
- `to_html()`: Appends new pass records to `index.html`.
- Handles simple file rotation (checks date change in file header).
- Applies visual formatting (e.g., red color for "Administration" passes).

### Entry Point

**bot.py**
- Sets up `Dispatcher`.
- Includes routers (`user`, `admin`, `events`).
- Registers bot commands (`/start`, `/help`, `/status`).
- Starts the `reset_sent_messages` background task.
- Initiates polling.

## Data Flow

### Registration Flow

```
/start → Check user in CHANNEL_ID
  ├─ User NOT in channel → Access Denied
  └─ User in channel
    ├─ ID in Database → Show "Order Pass" button
    └─ ID NOT in Database:
        → Request Contact
        → Contact Shared
        → Request Company
        → FIO Input
        → Save to Memory & File → Restart(/start)
```

### Pass Ordering Flow
```
Order button → Input pass details (vehicle/visitor)
  → Confirmation → Duplicate check
      ├─ Cancel → Reset State
      └─ Confirm → Anti-Flood Check
        ├─ Duplicate → Reject
        └─ Unique
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

1. **Hybrid Database**: Uses in-memory arrays for O(1)/O(n) speed during operation, syncing to disk on every write.
2. **Log Rotation**: Implemented via Python's `logging.handlers` to prevent disk overflow.
3. **Circular Import Prevention**: `Bot` instance moved to `config.py` to be accessible by both Routers and Services.
4. **Service Separation**: Logic for checking permissions and reading files separated from message handlers.
5. **HTML Export**: simple "append-only" logic for web-view of current passes.
