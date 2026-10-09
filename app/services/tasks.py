# app/services/tasks.py
from datetime import datetime

from app.memory.db import connect
from app.utils.time_utils import TZ


async def add_task(text: str, deadline: str | None = None) -> int:
    """deadline в ISO формате 'YYYY-MM-DD' или 'YYYY-MM-DD HH:MM' или None."""
    deadline_dt = None
    if deadline:
        try:
            # пробуем несколько форматов
            for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
                try:
                    deadline_dt = datetime.strptime(deadline, fmt).replace(tzinfo=TZ)
                    break
                except ValueError:
                    continue
        except Exception:
            deadline_dt = None

    async with connect() as db:
        cur = await db.execute(
            "INSERT INTO tasks(text, deadline) VALUES (?, ?)",
            (text, deadline_dt.isoformat() if deadline_dt else None),
        )
        await db.commit()
        return cur.lastrowid


async def list_tasks(only_open: bool = True) -> list[dict]:
    sql = "SELECT id, text, status, deadline, created_at FROM tasks"
    if only_open:
        sql += " WHERE status = 'open'"
    sql += " ORDER BY id"
    async with connect() as db:
        async with db.execute(sql) as cur:
            rows = await cur.fetchall()
    return [
        {"id": r[0], "text": r[1], "status": r[2], "deadline": r[3], "created_at": r[4]}
        for r in rows
    ]


async def complete_task(task_id: int) -> bool:
    async with connect() as db:
        cur = await db.execute(
            "UPDATE tasks SET status='done', closed_at=CURRENT_TIMESTAMP "
            "WHERE id = ? AND status='open'",
            (task_id,),
        )
        await db.commit()
        return cur.rowcount > 0


def format_tasks(tasks: list[dict]) -> str:
    if not tasks:
        return "(нет активных задач)"
    lines = []
    for t in tasks:
        deadline = f" | до {t['deadline']}" if t["deadline"] else ""
        lines.append(f"#{t['id']} {t['text']}{deadline}")
    return "\n".join(lines)