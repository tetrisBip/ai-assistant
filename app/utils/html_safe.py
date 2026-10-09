# app/utils/html_safe.py
"""
Подготовка текста от LLM к отправке в Telegram HTML.

Что делает:
  1. Конвертирует **жирный** → <b>жирный</b>
  2. Конвертирует __курсив__ → <i>курсив</i>
  3. Конвертирует `код` → <code>код</code>
  4. Экранирует оставшиеся <, >, & (чтобы Telegram не падал на «неизвестных тегах»)
  5. Оставляет наши разрешённые HTML-теги нетронутыми
"""
import re
from html import escape as html_escape


# Порядок важен: сначала `код`, потом **жирный**, потом __курсив__.
# Иначе ** может «съесть» кусок кода внутри.
_CODE_RE = re.compile(r"`([^`\n]+)`")
_BOLD_RE = re.compile(r"\*\*([^\*\n]+)\*\*")
_ITALIC_RE = re.compile(r"(?<!\w)__([^_\n]+)__(?!\w)")

# Разрешённые теги для Telegram
_ALLOWED_TAGS = ("b", "i", "u", "s", "code", "pre", "a", "tg-spoiler")


def _escape_outside_tags(text: str) -> str:
    """
    Экранирует & < > везде, кроме наших разрешённых тегов.
    Простой обход: сначала всё эскейпим, потом «возвращаем» разрешённые теги.
    """
    escaped = html_escape(text, quote=False)

    # Возвращаем обратно разрешённые теги
    for tag in _ALLOWED_TAGS:
        escaped = escaped.replace(f"&lt;{tag}&gt;", f"<{tag}>")
        escaped = escaped.replace(f"&lt;/{tag}&gt;", f"</{tag}>")
    return escaped


def safe(text: str) -> str:
    """
    Готовит текст LLM к отправке в Telegram с parse_mode='HTML'.
    Конвертирует базовый markdown в HTML, экранирует остальное.
    """
    if not text:
        return text

    # 1. Код в `обратных кавычках` — сначала, чтобы `**` внутри кода не съелся
    text = _CODE_RE.sub(lambda m: f"<code>{m.group(1)}</code>", text)

    # 2. **жирный** → <b>жирный</b>
    text = _BOLD_RE.sub(lambda m: f"<b>{m.group(1)}</b>", text)

    # 3. __курсив__ → <i>курсив</i>
    text = _ITALIC_RE.sub(lambda m: f"<i>{m.group(1)}</i>", text)

    # 4. Экранируем всё, что осталось опасным
    text = _escape_outside_tags(text)

    return text