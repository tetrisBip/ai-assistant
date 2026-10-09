# app/utils/logger.py
import logging
import sys
from pathlib import Path


def setup_logger(level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger("ai-assistant")
    if logger.handlers:
        return logger

    logger.setLevel(level.upper())
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # консоль
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    # файл (если есть папка data/logs)
    log_dir = Path("data/logs")
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_dir / "bot.log", encoding="utf-8")
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    except Exception:
        pass  # если нет прав — работаем только в консоль

    return logger


log = setup_logger()