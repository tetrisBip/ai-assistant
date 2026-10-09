# app/services/url_reader.py
import httpx
import trafilatura

from app.config import settings
from app.utils.logger import log


def fetch_text(url: str, max_chars: int = 8000) -> str:
    """Скачивает страницу через прокси и извлекает текст."""
    proxy = settings.llm_proxy or None
    try:
        with httpx.Client(proxy=proxy, timeout=30, follow_redirects=True) as client:
            r = client.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; AiAssistant/1.0)"},
            )
        if r.status_code != 200:
            return f"(HTTP {r.status_code} при загрузке {url})"
        html = r.text
    except Exception as e:
        log.warning(f"url download failed: {e}")
        return f"(ошибка загрузки: {e})"

    try:
        text = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=False,
            favor_precision=True,
        )
    except Exception as e:
        log.warning(f"trafilatura failed: {e}")
        return f"(ошибка разбора: {e})"

    if not text:
        return "(не удалось извлечь текст — возможно, это не статья)"
    if len(text) > max_chars:
        text = text[:max_chars] + "\n\n[...текст обрезан...]"
    return text