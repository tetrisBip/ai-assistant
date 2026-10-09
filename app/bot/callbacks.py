# app/bot/callbacks.py
"""
Callback-хендлеры для inline-кнопок:
- таблетки (pill:...)
- вечерний check-in (checkin:...)
"""
from app.imports import Router, CallbackQuery
from app.services.pills import (
    SLOT_MORNING, SLOT_EVENING, SLOT_LABELS, log_pill,
)
from app.scheduler.pills import repeated_pill_reminder
from app.scheduler.checkin import save_checkin
from app.utils.logger import log
import asyncio


router = Router(name="callbacks")


# =====================================================================
# Таблетки
# =====================================================================

@router.callback_query(lambda c: c.data and c.data.startswith("pill:"))
async def cb_pill(call: CallbackQuery) -> None:
    # pill:<slot>:<action>
    parts = call.data.split(":")
    if len(parts) != 3:
        await call.answer("Ошибка кнопки")
        return

    _, slot, action = parts
    if slot not in (SLOT_MORNING, SLOT_EVENING):
        await call.answer("Неизвестный слот")
        return

    label = SLOT_LABELS[slot]

    if action == "yes":
        await log_pill(slot, taken=True)
        await call.answer(f"{label}: принято ✅")
        try:
            await call.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        await call.message.answer(f"Записала: {label} — выпил(а) ✅")
        return

    if action == "no":
        await log_pill(slot, taken=False)
        await call.answer(f"{label}: пропущено ❌")
        try:
            await call.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        await call.message.answer(
            f"Записала: {label} — пропустил(а). "
            "Если это про постоянный приём — стоит упомянуть врачу."
        )
        return

    if action == "later":
        await call.answer("Ок, напомню через 30 минут")
        try:
            await call.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        # отложенное напоминание — планируем через 30 минут
        async def _later():
            await asyncio.sleep(30 * 60)
            try:
                await repeated_pill_reminder(call.bot, call.from_user.id, slot)
            except Exception as e:
                log.warning(f"later reminder failed: {e}")

        asyncio.create_task(_later())
        return

    await call.answer("Неизвестное действие")


# =====================================================================
# Check-in
# =====================================================================

@router.callback_query(lambda c: c.data and c.data.startswith("checkin:mood:"))
async def cb_checkin_mood(call: CallbackQuery) -> None:
    mood = call.data.rsplit(":", 1)[1]
    mood_labels = {"good": "хорошо", "meh": "так себе", "bad": "плохо"}
    if mood not in mood_labels:
        await call.answer("Неизвестное настроение")
        return

    await save_checkin(mood=mood, summary=None)
    await call.answer(f"Записала: {mood_labels[mood]}")
    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await call.message.answer(
        f"Понятно. Если хочешь — расскажи подробнее, что было. 🙂"
    )