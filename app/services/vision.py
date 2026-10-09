# app/services/vision.py
"""
Отправка изображения в vision-модель (Qwen VL через OpenRouter).
"""
import base64
from pathlib import Path

from app.llm import llm
from app.utils.logger import log


VISION_SYSTEM = (
    "Ты — помощник, который смотрит картинки. Отвечай по-русски, "
    "конкретно и по делу. Если это скриншот кода, логов, конфига, "
    "ошибки или дашборда — разбери, что там, и предложи решение, если уместно. "
    "Если это фото (не скрин) — опиши, что видишь, и ответь на вопрос. "
    "Не выдумывай детали, которых не видно."
)


def _encode_image(path: Path) -> tuple[str, str]:
    """Возвращает (base64_data, mime_type)."""
    suffix = path.suffix.lower().lstrip(".")
    mime = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
        "gif": "image/gif",
        "bmp": "image/bmp",
    }.get(suffix, "image/jpeg")

    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return data, mime


async def ask_vision(image_path: Path, question: str) -> str:
    """
    Отправляет картинку + вопрос в vision-модель.
    Возвращает ответ модели или строку с ошибкой.
    """
    try:
        b64, mime = _encode_image(image_path)
    except Exception as e:
        log.exception("vision: encode failed")
        return f"Не смогла прочитать картинку: {e}"

    if not question.strip():
        question = "Что на этой картинке? Если это технический контент — разбери его."

    messages = [
        {"role": "system", "content": VISION_SYSTEM},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": question},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime};base64,{b64}"},
                },
            ],
        },
    ]

    try:
        result = await llm.vision_chat(messages)
    except Exception as e:
        log.exception("vision: LLM call failed")
        return f"⚠ Vision-модель недоступна: {type(e).__name__}: {e}"

    return (result.get("content") or "").strip() or "(пустой ответ vision-модели)"