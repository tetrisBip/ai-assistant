# app/bot/handlers.py
from app.imports import Router, Message, ChatAction, F, TelegramBadRequest
from app.services.chat import respond
from app.services.telegram_files import handle_document, handle_voice
from app.services.file_reader import FileReadError
from app.utils.html_safe import safe
from app.utils.logger import log

router = Router(name="handlers")

async def _reply(message: Message, prompt_for_llm: str) -> None:
    """Отправить запрос в LLM и вернуть ответ, экранируя HTML."""
    status_msg = None

    async def on_progress(text: str) -> None:
        nonlocal status_msg
        try:
            if status_msg is None:
                status_msg = await message.answer(text)
            else:
                await status_msg.edit_text(text)
        except Exception as e:
            log.debug(f"progress update failed: {e}")

    try:
        await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
        answer = await respond(prompt_for_llm, on_progress=on_progress)
    except Exception as e:
        log.exception("respond() failed")
        await message.answer(f"⚠ Ошибка: {type(e).__name__}: {e}")
        return

    # удаляем промежуточный статус
    if status_msg is not None:
        try:
            await status_msg.delete()
        except Exception:
            pass

    try:
        await message.answer(safe(answer))
    except TelegramBadRequest as e:
        log.warning(f"HTML send failed, fallback to plain: {e}")
        await message.answer(answer, parse_mode=None)

@router.message(F.text)
async def text_handler(message: Message) -> None:
    log.info(f"<- text: {message.text[:200]!r}")

    # Если сегодня был отправлен check-in и ответа ещё нет — сохраняем summary
    try:
        from app.memory.db import connect
        from app.utils.time_utils import today_str
        from app.scheduler.checkin import save_checkin

        async with connect() as db:
            async with db.execute(
                "SELECT summary FROM daily_checkins WHERE date = ?",
                (today_str(),),
            ) as cur:
                row = await cur.fetchone()

        # Если строка есть, но summary пустой — значит ответили кнопкой настроения,
        # а сейчас пишут подробнее. Сохраняем текст как summary.
        if row is not None and not row[0]:
            await save_checkin(mood=None, summary=message.text[:500])
    except Exception as e:
        log.warning(f"checkin summary save failed: {e}")

    await _reply(message, message.text)


@router.message(F.document)
async def document_handler(message: Message) -> None:
    log.info(f"<- document: {message.document.file_name}")
    try:
        prompt = await handle_document(message.bot, message.document)
    except FileReadError as e:
        await message.answer(f"Не смогла обработать файл: {e}")
        return
    except Exception as e:
        log.exception("document handling failed")
        await message.answer(f"⚠ Ошибка при обработке файла: {e}")
        return
    await _reply(message, prompt)


@router.message(F.voice)
async def voice_handler(message: Message) -> None:
    log.info("<- voice")
    try:
        prompt = await handle_voice(message.bot, message.voice)
    except Exception as e:
        log.exception("voice handling failed")
        await message.answer(f"⚠ Ошибка при распознавании голоса: {e}")
        return
    await _reply(message, prompt)


@router.message()
async def fallback_handler(message: Message) -> None:
    # фото, стикеры, видео и прочее
    await message.answer(
        "Пока я понимаю текст, файлы и голосовые. Фото временно не обрабатываю."
    )