# app/services/pills.py
"""
Учёт приёма таблеток.
Слоты: 'morning' (утренняя таблетница, 12:10) и 'evening' (вечерняя, 22:20).
"""
from datetime import datetime

from app.memory.db import connect
from app.utils.time_utils import now, today_str, TZ


SLOT_MORNING = "morning"
SLOT_EVENING = "evening"

SLOT_LABELS = {
    SLOT_MORNING: "утренняя таблетница",
    SLOT_EVENING: "вечерняя таблетница",
}


async def log_pill(slot: str, taken: bool) -> None:
    """Записать факт приёма/пропуска таблеток за сегодня."""
    today = today_str()
    async with connect() as db:
        await db.execute(
            """
            INSERT INTO pills_log(date, slot, taken, answered_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(date, slot) DO UPDATE SET
                taken = excluded.taken,
                answered_at = CURRENT_TIMESTAMP
            """,
            (today, slot, 1 if taken else 0),
        )
        await db.commit()


async def get_pill_status(slot: str, date: str | None = None) -> int | None:
    """
    Возвращает:
      None — нет записи (не отвечали),
      1 — принял,
      0 — пропустил.
    """
    date = date or today_str()
    async with connect() as db:
        async with db.execute(
            "SELECT taken FROM pills_log WHERE date = ? AND slot = ?",
            (date, slot),
        ) as cur:
            row = await cur.fetchone()
    if not row:
        return None
    return row[0]


async def get_today_status() -> dict:
    """Сводка за сегодня по обоим слотам."""
    return {
        SLOT_MORNING: await get_pill_status(SLOT_MORNING),
        SLOT_EVENING: await get_pill_status(SLOT_EVENING),
    }


def status_icon(value: int | None) -> str:
    if value == 1:
        return "✅"
    if value == 0:
        return "❌"
    return "—"


async def format_today_status() -> str:
    """Человекочитаемая сводка для /pills."""
    st = await get_today_status()
    lines = [
        "<b>Таблетки сегодня:</b>",
        f"  {status_icon(st[SLOT_MORNING])} Утро (12:10)",
        f"  {status_icon(st[SLOT_EVENING])} Вечер (22:20)",
    ]
    return "\n".join(lines)