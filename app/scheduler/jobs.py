# app/scheduler/jobs.py
from app.imports import AsyncIOScheduler, CronTrigger, Bot
from app.config import settings
from app.utils.logger import log
from app.utils.time_utils import TZ, parse_hhmm

from app.scheduler.pills import send_pill_reminder
from app.scheduler.checkin import send_checkin
from app.services.pills import SLOT_MORNING, SLOT_EVENING


def register_jobs(scheduler: AsyncIOScheduler, bot: Bot) -> None:
    owner_id = settings.owner_id

    # --- Таблетки: утренняя ---
    h, m = parse_hhmm(settings.pills_morning)
    scheduler.add_job(
        send_pill_reminder,
        CronTrigger(hour=h, minute=m, timezone=TZ),
        args=[bot, owner_id, SLOT_MORNING],
        id="pills_morning",
        replace_existing=True,
    )

    # --- Таблетки: вечерняя ---
    h, m = parse_hhmm(settings.pills_evening)
    scheduler.add_job(
        send_pill_reminder,
        CronTrigger(hour=h, minute=m, timezone=TZ),
        args=[bot, owner_id, SLOT_EVENING],
        id="pills_evening",
        replace_existing=True,
    )

    # --- Вечерний check-in ---
    h, m = parse_hhmm(settings.checkin_time)
    scheduler.add_job(
        send_checkin,
        CronTrigger(hour=h, minute=m, timezone=TZ),
        args=[bot, owner_id],
        id="checkin",
        replace_existing=True,
    )

    log.info(
        f"Scheduler jobs registered: "
        f"pills {settings.pills_morning} & {settings.pills_evening}, "
        f"checkin {settings.checkin_time} (TZ={TZ})"
    )