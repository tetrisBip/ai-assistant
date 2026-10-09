# app/llm/prompts.py
from pathlib import Path

from app.utils.time_utils import now
from app.memory.profile import get_all_facts, facts_to_prompt

PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"


def _read(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")


async def build_system_prompt() -> str:
    facts = await get_all_facts()
    name = facts.get("name", "пользователь")

    base = _read("system.md")
    sysadmin = _read("sysadmin.md")

    now_dt = now()
    return base.format(
        name=name,
        facts=facts_to_prompt(facts),
        now=now_dt.strftime("%Y-%m-%d %H:%M (%A)"),
        year=now_dt.year,
        month=now_dt.month,
        day=now_dt.day,
    ) + "\n\n" + sysadmin