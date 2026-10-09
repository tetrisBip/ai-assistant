# app/llm/client.py
from app.config import settings
from app.utils.logger import log
from app.llm.groq_provider import GroqProvider
from app.llm.openrouter_provider import OpenRouterProvider


class LLMClient:
    """
    Единая точка входа к LLM.

      chat()        — текст:
        1. Groq (gpt-oss-20b из .env)
        2. Groq (llama-3.1-8b-instant — у модели свои лимиты)
        3. OpenRouter (fallback_model из .env)
      vision_chat() — картинки: OpenRouter vision-модель
    """

    # резервная модель внутри Groq — у каждой модели свои лимиты
    GROQ_FALLBACK_MODEL = "openai/gpt-oss-120b"   # или qwen/qwen3.8-27b

    def __init__(self) -> None:
        self.groq = GroqProvider()
        self.openrouter = OpenRouterProvider() if settings.openrouter_api_key else None

    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        temperature: float = 0.7,
    ) -> dict:
        # 1. Основная
        try:
            return await self.groq.chat(messages, tools=tools, temperature=temperature)
        except Exception as e:
            log.warning(f"Groq ({settings.groq_model}) failed: {e}")

        # 2. Резерв внутри Groq
        try:
            log.info(f"Fallback → Groq/{self.GROQ_FALLBACK_MODEL}")
            return await self.groq.chat_with_model(
                messages,
                model=self.GROQ_FALLBACK_MODEL,
                tools=tools,
                temperature=temperature,
            )
        except Exception as e:
            log.warning(f"Groq fallback ({self.GROQ_FALLBACK_MODEL}) failed: {e}")

        # 3. Внешний резерв — OpenRouter
        if self.openrouter and settings.fallback_model:
            try:
                log.info(f"Fallback → OpenRouter/{settings.fallback_model}")
                return await self.openrouter.chat(
                    messages,
                    model=settings.fallback_model,
                    tools=tools,
                    temperature=temperature,
                )
            except Exception as e:
                log.warning(f"OpenRouter fallback failed: {e}")

        raise RuntimeError("All text LLM providers failed")

    async def vision_chat(
        self,
        messages: list[dict],
        temperature: float = 0.3,
    ) -> dict:
        if not self.openrouter:
            raise RuntimeError("OpenRouter не настроен (нет OPENROUTER_API_KEY)")

        return await self.openrouter.chat(
            messages,
            model=settings.vision_model,
            tools=None,
            temperature=temperature,
        )


llm = LLMClient()