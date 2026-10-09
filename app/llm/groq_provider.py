# app/llm/groq_provider.py
import httpx
from openai import AsyncOpenAI

from app.config import settings
from app.utils.logger import log


class GroqProvider:
    """Groq через OpenAI-совместимый API."""

    name = "groq"
    supports_vision = False

    def __init__(self) -> None:
        http_client = None
        if settings.llm_proxy:
            http_client = httpx.AsyncClient(proxy=settings.llm_proxy, timeout=60.0)
            log.info(f"Groq proxy: {settings.llm_proxy}")
        else:
            log.info("Groq proxy: disabled")

        self.client = AsyncOpenAI(
            api_key=settings.groq_api_key,
            base_url="https://api.groq.com/openai/v1",
            timeout=60.0,
            http_client=http_client,
        )
        self.model = settings.groq_model

    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        temperature: float = 0.7,
    ) -> dict:
        return await self._chat_with_model(
            messages,
            model=self.model,
            tools=tools,
            temperature=temperature,
        )

    async def chat_with_model(
        self,
        messages: list[dict],
        model: str,
        tools: list[dict] | None = None,
        temperature: float = 0.7,
    ) -> dict:
        """Тот же чат, но с переопределением модели (для fallback внутри Groq)."""
        return await self._chat_with_model(
            messages,
            model=model,
            tools=tools,
            temperature=temperature,
        )

    async def _chat_with_model(
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