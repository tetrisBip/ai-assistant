# app/memory/messages.py
from app.memory.db import connect


async def add_message(role: str, content: str) -> None:
    async with connect() as db:
        await db.execute(
            "INSERT INTO messages(role, content) VALUES (?, ?)",
            (role, content),
        )
        await db.commit()


async def get_recent_messages(limit: int = 20, max_chars: int = 800) -> list[dict]:
    """
    Последние N сообщений в хронологическом порядке (старые → новые).
    Длинные сообщения обрезаются до max_chars — экономия токенов.
    """
    async with connect() as db:
        async with db.execute(
            "SELECT role, content FROM messages ORDER BY id DESC LIMIT ?",
            (limit,),
        ) as cur:
            rows = await cur.fetchall()
    rows.reverse()

    out = []
    for role, content in rows:
        if len(content) > max_chars:
            content = content[:max_chars] + " […обрезано]"
        out.append({"role": role, "content": content})
    return out


async def clear_messages() -> None:
    async with connect() as db:
        await db.execute("DELETE FROM messages")
        await db.commit()