# tools/list_free_models.py
"""
Показывает бесплатные текстовые модели на OpenRouter.
Запуск: python -m tools.list_free_models
"""
import asyncio
import httpx
from app.config import settings


async def main():
    async with httpx.AsyncClient(proxy=settings.llm_proxy or None, timeout=30) as c:
        r = await c.get(
            "https://openrouter.ai/api/v1/models",
            headers={"Authorization": f"Bearer {settings.openrouter_api_key}"},
        )
    if r.status_code != 200:
        print(f"HTTP {r.status_code}: {r.text[:300]}")
        return

    data = r.json().get("data", [])
    free = []
    for m in data:
        if ":free" not in m["id"]:
            continue
        modalities = m.get("architecture", {}).get("input_modalities", [])
        if "text" not in modalities:
            continue
        ctx = m.get("context_length", 0)
        free.append((m["id"], ctx))

    if not free:
        print("(нет бесплатных текстовых моделей)")
        return

    print(f"Найдено {len(free)} бесплатных текстовых моделей:\n")
    for mid, ctx in free:
        print(f"  {mid}    ctx={ctx}")


if __name__ == "__main__":
    asyncio.run(main())