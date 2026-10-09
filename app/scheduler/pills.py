# app/scheduler/pills.py
"""
Задачи планировщика для напоминаний о таблетках.
12:10 — утренняя, 22:20 — вечерняя.
"""
from datetime import timedelta

from app.imports import Bot, InlineKeyboardMarkup, InlineKeyboardButton
from app.llm import llm
from app.services.pills import (
    SLOT_MORNING, SLOT_EVENING, SLOT_LABELS,
    get_pill_status, status_icon,
)
from app.utils.time_utils import now, today_str
from app.memory.profile import get_fact
from app.utils.logger import log


# Хранилище «напоминание ещё раз через 30 минут» — в памяти процесса.
# Ключ: (slot, message_id) → сколько раз уже напоминали.
_pending: dict[tuple[str, int], int] = {}


def pills_keyboard(slot: str) -> InlineKeyboardMarkup:
    """Кнопки под напоминанием о таблетках."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Выпил", callback_data=f"pill:{slot}:yes"),
                InlineKeyboardButton(text="⏳ Позже", callback_data=f"pill:{slot}:later"),
                InlineKeyboardButton(text="❌ Пропустил", callback_data=f"pill:{slot}:no"),
            ]
        ]
    )


async def _build_pill_message(slot: str) -> str:
    """Генерит текст напоминания через LLM."""
    from pathlib import Path
    import asyncio

    prompts_dir = Path(__file__).resolve().parent.parent.parent / "prompts"
    template = (prompts_dir / "pills.md").read_text(encoding="utf-8")

    current_hour = now().hour
    if current_hour < 17:
        day_phase = "сейчас день, впереди ещё дела"
    else:
        day_phase = "вечер, скоро спать"

    yesterday = (now() - timedelta(days=1)).strftime("%Y-%m-%d")
    y_status_raw = await get_pill_status(slot, yesterday)
    y_status = {
        1: "выпил",
        0: "пропустил",
        None: "не было ответа",
    }[y_status_raw]

    name = await get_fact("name") or "пользователь"

    prompt = template.format(
        slot_label=SLOT_LABELS[slot],
        name=name,
        day_phase=day_phase,
        yesterday_status=y_status,
    )

    try:
        result = await llm.chat(
            [{"role": "user", "content": prompt}],
            temperature=0.8,
        )
        text = (result.get("content") or "").strip()
        if text:
            return text
    except Exception as e:
        log.warning(f"pill message generation failed: {e}")

    # Fallback, если LLM не ответила
    if slot == SLOT_MORNING:
        return "Утро. Пора выпить таблетки из утренней таблетницы. 💊"
    return "Вечер. Не забудь про вечернюю таблетницу. 💊"


async def send_pill_reminder(bot: Bot, owner_id: int, slot: str) -> None:
    """Отправить напоминание в чат."""
    # Если уже ответили на этот слот сегодня — не дёргаем
    already = await get_pill_status(slot)
    if already is not None:
        log.info(f"pills/{slot}: already answered today, skip")
        return

    text = await _build_pill_message(slot)
    msg = await bot.send_message(
        chat_id=owner_id,
        text=text,
        reply_markup=pills_keyboard(slot),
    )
    log.info(f"pills/{slot}: reminder sent, message_id={msg.message_id}")


async def repeated_pill_reminder(bot: Bot, owner_id: int, slot: str) -> None:
    """Повторное напоминание (через 30 минут после 'Позже')."""
    already = await get_pill_status(slot)
    if already is not None:
        return

    text = f"Напоминаю про {SLOT_LABELS[slot]}. 💊"
    await bot.send_message(
        chat_id=owner_id,
        text=text,
        reply_markup=pills_keyboard(slot),
    )
    log.info(f"pills/{slot}: repeat reminder sent")