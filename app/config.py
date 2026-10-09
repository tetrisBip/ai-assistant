# app/config.py
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # === Telegram ===
    telegram_token: str
    owner_id: int
    telegram_proxy: str = ""

    # === Основной LLM: Groq ===
    groq_api_key: str
    groq_model: str = "openai/gpt-oss-120b"

    # === OpenRouter: vision + fallback ===
    openrouter_api_key: str = ""
    vision_model: str = "qwen/qwen2.5-vl-72b-instruct:free"
    fallback_model: str = "nvidia/nemotron-3-super-120b-a12b:free"

    # === Общий прокси для LLM ===
    llm_proxy: str = ""

    # === Время и напоминания ===
    tz: str = "Europe/Moscow"
    pills_morning: str = "12:10"
    pills_evening: str = "22:20"
    checkin_time: str = "22:00"

    # === Поиск ===
    search_provider: str = "tavily"
    tavily_api_key: str = ""
    brave_api_key: str = ""

    # === Прочее ===
    log_level: str = "INFO"
    db_path: str = "data/assistant.db"
    dry_run: bool = False

    @property
    def db_full_path(self) -> Path:
        p = Path(self.db_path)
        return p if p.is_absolute() else BASE_DIR / p


settings = Settings()