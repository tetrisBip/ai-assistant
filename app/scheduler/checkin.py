# app/scheduler/checkin.py
"""
Вечерний check-in в 22:00.
Спрашиваем о дне — живо, с учётом контекста.
"""
from pathlib import Path
from datetime import timedelta

from app.imports import Bot, InlineKeyboardMarkup, InlineKeyboardButton
from app.llm import llm
from app.memory import messages as msg_store
from app.memory.db import connect
from app.memory.profile import get_fact
from app.services.pills import (
    SLOT_MORNING, SLOT_EVENING, get_pill_status, status_icon,
)
from app.utils.time_utils import now, today_str
from app.utils.logger import log


def checkin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="😊 Хорошо", callback_data="checkin:mood:good"),
                InlineKeyboardButton(text="😐 Так себе", callback_data="checkin:mood:meh"),
                InlineKeyboardButton(text="😔 Плохо", callback_data="checkin:mood:bad"),
            ],
        ]
    )


async def _get_yesterday_summary() -> str:
    yesterday = (now() - timedelta(days=1)).strftime("%Y-%m-%d")
    async with connect() as db:
        async with db.execute(
            "SELECT summary, mood FROM daily_checkins WHERE date = ?",
            (yesterday,),
        ) as cur:
            row = await cur.fetchone()
    if not row:
        return "(нет записи за вчера)"
    summary, mood = row
    return f"{summary or '(без описания)'} (настроение: {mood or 'не указано'})"


async def _get_recent_topics(limit: int = 10) -> str:
    """Последние user-сообщения — чтобы понять, о чём был разговор."""
    msgs = await msg_store.get_recent_messages(limit=limit)
    user_lines = [m["content"][:120] for m in msgs if m["role"] == "user"]
    if not user_lines:
        return "(история пуста)"
    return " | ".join(user_lines[-5:])


async def build_checkin_text() -> str:
    prompts_dir = Path(__file__).resolve().parent.parent.parent / "prompts"
    template = (prompts_dir / "checkin.md").read_text(encoding="utf-8")

    name = await get_fact("name") or "пользователь"
    yesterday_summary = await _get_yesterday_summary()
    recent_topics = await _get_recent_topics()

    morning = await get_pill_status(SLOT_MORNING)
    evening = await get_pill_status(SLOT_EVENING)

    prompt = template.format(
        name=name,
        yesterday_summary=yesterday_summary,
        recent_topics=recent_topics,
        pill_morning=status_icon(morning),
        pill_evening=status_icon(evening),
    )

    try:
        result = await llm.chat(
            [{"role": "user", "content": prompt}],
            temperature=0.85,
        )
        text = (result.get("content") or "").strip()
        if text:
            return text
    except Exception as e:
        log.warning(f"checkin generation failed: {e}")

    return "Привет. Как прошёл день?"


async def send_checkin(bot: Bot, owner_id: int) -> None:
    text = await build_checkin_text()
    await bot.send_message(
        chat_id=owner_id,
        text=text,
        reply_markup=checkin_keyboard(),
    )
    log.info("checkin: sent")


async def save_checkin(mood: str | None, summary: str | None) -> None:
    """Сохранить ответ на check-in. mood: good/meh/bad. summary: свободный текст."""
    today = today_str()
    async with connect() as db:
        await db.execute(
            """
            INSERT INTO daily_checkins(date, mood, summary)
            VALUES (?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET
                mood = COALESCE(excluded.mood, daily_checkins.mood),
                summary = COALESCE(excluded.summary, daily_checkins.summary)
            """,
            (today, mood, summary),
        )
        await db.commit()