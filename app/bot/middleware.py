# app/bot/middleware.py
from typing import Any, Callable, Awaitable

from app.imports import BaseMiddleware, TelegramObject
from app.config import settings
from app.utils.logger import log


class OwnerOnlyMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user is None or user.id != settings.owner_id:
            if user is not None:
                log.warning(f"Ignored message from user_id={user.id} (@{user.username})")
            return None
        return await handler(event, data)