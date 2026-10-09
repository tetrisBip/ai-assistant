# app/llm/openrouter_provider.py
import httpx
from openai import AsyncOpenAI

from app.config import settings
from app.utils.logger import log


class OpenRouterProvider:
    """
    OpenRouter — OpenAI-совместимый API.
    Используется для:
      * vision-моделей (модель задаётся при вызове)
      * fallback для текста (модель = settings.fallback_model)
    """

    name = "openrouter"

    def __init__(self) -> None:
        http_client = None
        if settings.llm_proxy:
            http_client = httpx.AsyncClient(proxy=settings.llm_proxy, timeout=90.0)
            log.info(f"OpenRouter proxy: {settings.llm_proxy}")
        else:
            log.info("OpenRouter proxy: disabled")

        self.client = AsyncOpenAI(
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
            timeout=90.0,
            http_client=http_client,
        )

    async def chat(
        self,
        messages: list[dict],
        model: str,
        tools: list[dict] | None = None,
        temperature: float = 0.7,
    ) -> dict:
        kwargs: dict = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        resp = await self.client.chat.completions.create(**kwargs)

        # Защита от пустого ответа — было 'NoneType' object is not subscriptable
        if resp is None or not getattr(resp, "choices", None):
            raise RuntimeError(
                f"OpenRouter вернул пустой ответ для модели {model}"
            )

        msg = resp.choices[0].message
        return {
            "content": msg.content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                }
                for tc in (msg.tool_calls or [])
            ],
            "raw": msg,
        }