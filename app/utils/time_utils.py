# app/utils/time_utils.py
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo


TZ = ZoneInfo("Europe/Moscow")


def now() -> datetime:
    return datetime.now(TZ)


def today_str() -> str:
    return now().strftime("%Y-%m-%d")


def parse_hhmm(s: str) -> tuple[int, int]:
    """'12:10' -> (12, 10). Бросает ValueError при неверном формате."""
    h, m = s.strip().split(":")
    return int(h), int(m)


def hhmm_to_time(s: str) -> dtime:
    h, m = parse_hhmm(s)
    return dtime(hour=h, minute=m, tzinfo=TZ)