# app/main.py
import asyncio

from app.imports import (
    Bot, Dispatcher, DefaultBotProperties, ParseMode,
    AsyncIOScheduler, BotCommand,
)
from app.config import settings
from app.utils.logger import log
from app.utils.time_utils import TZ
from app.memory.db import init_db
from app.bot import commands_router, handlers_router, OwnerOnlyMiddleware
from app.scheduler import register_jobs


async def main() -> None:
    log.info("Starting ai-assistant bot...")

    # 1) БД
    await init_db()

    # 2) Telegram Bot (+ опциональный прокси)
    session = None
    if settings.telegram_proxy:
        from aiogram.client.session.aiohttp import AiohttpSession
        session = AiohttpSession(proxy=settings.telegram_proxy)
        log.info(f"Telegram proxy: {settings.telegram_proxy}")
    else:
        log.info("Telegram proxy: disabled (direct)")

    bot = Bot(
        token=settings.telegram_token,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # 3) Middleware — только владелец
    dp.message.middleware(OwnerOnlyMiddleware())
    dp.callback_query.middleware(OwnerOnlyMiddleware())

       # 4) Роутеры
    from app.bot import callbacks_router
    dp.include_router(commands_router)
    dp.include_router(callbacks_router)
    dp.include_router(handlers_router)
    
    # 5) Планировщик
    scheduler = AsyncIOScheduler(timezone=TZ)
    register_jobs(scheduler, bot)
    scheduler.start()
    log.info(f"Scheduler started (TZ={TZ})")

    # 6) Меню команд (только если не dry-run)
    if not settings.dry_run:
        try:
            await bot.set_my_commands([
                BotCommand(command="help",     description="Что я умею"),
                BotCommand(command="profile",  description="Что я о тебе знаю"),
                BotCommand(command="remember", description="Запомнить факт (key=value)"),
                BotCommand(command="forget",   description="Удалить факт (key)"),
                BotCommand(command="tasks",    description="Активные задачи"),
                BotCommand(command="pills",    description="Статус таблеток"),
                BotCommand(command="checkin",  description="Вечерний разговор"),
                BotCommand(command="reset",    description="Сбросить контекст диалога"),
            ])
        except Exception as e:
            log.warning(f"set_my_commands failed: {e}")
    else:
        log.info("DRY_RUN=true: skipping set_my_commands")

    # 7) Запуск
    if settings.dry_run:
        log.info("DRY_RUN=true: Telegram polling disabled. Ctrl+C to stop.")
        try:
            while True:
                await asyncio.sleep(3600)
        except asyncio.CancelledError:
            pass
    else:
        log.info("Polling started.")
        try:
            await dp.start_polling(bot)
        finally:
            scheduler.shutdown(wait=False)
            await bot.session.close()
            log.info("Bot stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        log.info("Interrupted by user.")