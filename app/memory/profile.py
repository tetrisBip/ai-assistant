# app/memory/profile.py
from app.memory.db import connect


async def set_fact(key: str, value: str) -> None:
    async with connect() as db:
        await db.execute(
            """
            INSERT INTO profile(key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = CURRENT_TIMESTAMP
            """,
            (key, value),
        )
        await db.commit()


async def get_fact(key: str) -> str | None:
    async with connect() as db:
        async with db.execute(
            "SELECT value FROM profile WHERE key = ?", (key,)
        ) as cur:
            row = await cur.fetchone()
    return row[0] if row else None


async def get_all_facts() -> dict[str, str]:
    async with connect() as db:
        async with db.execute("SELECT key, value FROM profile") as cur:
            rows = await cur.fetchall()
    return {k: v for k, v in rows}


async def delete_fact(key: str) -> bool:
    async with connect() as db:
        cur = await db.execute("DELETE FROM profile WHERE key = ?", (key,))
        await db.commit()
        return cur.rowcount > 0


def facts_to_prompt(facts: dict[str, str]) -> str:
    if not facts:
        return "(пока ничего не известно)"
    return "\n".join(f"- {k}: {v}" for k, v in facts.items())