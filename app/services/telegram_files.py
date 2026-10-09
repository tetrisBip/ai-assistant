# app/services/telegram_files.py
"""
Скачивание файлов из Telegram и обработка.
Голос/аудио — через Groq Whisper.
Картинки в этом модуле только скачиваются — их обработка в app/services/vision.py.
"""
import asyncio
import tempfile
from pathlib import Path

from aiogram import Bot
from aiogram.types import Document, PhotoSize, Voice

from app.services.file_reader import extract_text, FileReadError
from app.utils.logger import log


MAX_TELEGRAM_FILE_SIZE = 20 * 1024 * 1024  # Bot API: 20 МБ на скачивание


async def download_document(bot: Bot, doc: Document) -> Path:
    if doc.file_size and doc.file_size > MAX_TELEGRAM_FILE_SIZE:
        raise FileReadError(
            f"файл слишком большой ({doc.file_size} байт), лимит 20 МБ"
        )
    tg_file = await bot.get_file(doc.file_id)
    suffix = Path(doc.file_name or "file").suffix or ""
    tmp = Path(tempfile.mkstemp(suffix=suffix)[1])
    await bot.download_file(tg_file.file_path, destination=tmp)
    return tmp


async def download_photo(bot: Bot, photo: PhotoSize) -> Path:
    tg_file = await bot.get_file(photo.file_id)
    tmp = Path(tempfile.mkstemp(suffix=".jpg")[1])
    await bot.download_file(tg_file.file_path, destination=tmp)
    return tmp


async def download_voice(bot: Bot, voice: Voice) -> Path:
    tg_file = await bot.get_file(voice.file_id)
    tmp = Path(tempfile.mkstemp(suffix=".ogg")[1])
    await bot.download_file(tg_file.file_path, destination=tmp)
    return tmp


async def handle_document(bot: Bot, doc: Document) -> str:
    path = await download_document(bot, doc)
    try:
        try:
            text = await asyncio.to_thread(extract_text, path)
            return f"Пользователь прислал файл {doc.file_name}:\n\n{text}"
        except FileReadError as e:
            return f"Пользователь прислал файл {doc.file_name}, но прочитать не удалось: {e}"
    finally:
        path.unlink(missing_ok=True)


async def handle_voice(bot: Bot, voice: Voice) -> str:
    path = await download_voice(bot, voice)
    try:
        text = await _transcribe_with_groq(path)
        return f"Пользователь отправил голосовое сообщение. Транскрипт:\n\n{text}"
    finally:
        path.unlink(missing_ok=True)


async def _transcribe_with_groq(path: Path) -> str:
    import httpx
    from app.config import settings

    url = "https://api.groq.com/openai/v1/audio/transcriptions"
    headers = {"Authorization": f"Bearer {settings.groq_api_key}"}
    proxy = settings.llm_proxy or None

    with path.open("rb") as f:
        files = {"file": (path.name, f, "audio/ogg")}
        data = {"model": "whisper-large-v3", "language": "ru"}

        async with httpx.AsyncClient(proxy=proxy, timeout=120) as client:
            r = await client.post(url, headers=headers, files=files, data=data)

    if r.status_code != 200:
        log.warning(f"Whisper failed: {r.status_code} {r.text[:200]}")
        return f"(не удалось распознать голосовое: HTTP {r.status_code})"

    return r.json().get("text", "").strip() or "(пустой транскрипт)"