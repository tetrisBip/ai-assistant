# app/memory/db.py
from pathlib import Path
import aiosqlite

from app.config import settings
from app.utils.logger import log


SCHEMA = """
-- История диалога
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL,               -- user / assistant / tool
    content TEXT NOT NULL,
    ts DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_messages_ts ON messages(ts);

-- Факты о пользователе
CREATE TABLE IF NOT EXISTS profile (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Напоминания (общий список, для гибкости)
CREATE TABLE IF NOT EXISTS reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    time TEXT NOT NULL,               -- "HH:MM"
    days TEXT NOT NULL DEFAULT 'daily',
    active INTEGER NOT NULL DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Лог приёма таблеток
CREATE TABLE IF NOT EXISTS pills_log (
    date TEXT NOT NULL,               -- "YYYY-MM-DD"
    slot TEXT NOT NULL,               -- "morning" | "evening"
    taken INTEGER,                    -- 1 / 0 / NULL (нет ответа)
    answered_at DATETIME,
    PRIMARY KEY (date, slot)
);

-- Рабочие задачи
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',   -- open / done
    deadline DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    closed_at DATETIME
);

-- Ежедневные check-in
CREATE TABLE IF NOT EXISTS daily_checkins (
    date TEXT PRIMARY KEY,
    mood TEXT,
    summary TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""


async def init_db() -> None:
    path: Path = settings.db_full_path
    path.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(path) as db:
        await db.executescript(SCHEMA)
        await db.commit()
    log.info(f"DB initialized: {path}")


def connect() -> aiosqlite.Connection:
    """Возвращает соединение. Использовать через 'async with'."""
    return aiosqlite.connect(settings.db_full_path)