# app/bot/__init__.py
from app.bot.commands import router as commands_router
from app.bot.handlers import router as handlers_router
from app.bot.callbacks import router as callbacks_router
from app.bot.middleware import OwnerOnlyMiddleware

__all__ = [
    "commands_router",
    "handlers_router",
    "callbacks_router",
    "OwnerOnlyMiddleware",
]