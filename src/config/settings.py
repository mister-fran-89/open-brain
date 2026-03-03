from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from pathlib import Path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    # Storage
    vault_path: Path = Field(default=Path("/vault"))
    data_path: Path = Field(default=Path("/data"))

    # AI Providers
    ollama_host: str = "http://ollama:11434"
    gemini_api_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # AI Routing
    ai_classify_provider: str = "ollama"
    ai_embed_provider: str = "ollama"
    ai_query_provider: str = "ollama"
    ai_summarize_provider: str = "ollama"

    # Models
    ollama_classify_model: str = "phi3:mini"
    ollama_embed_model: str = "nomic-embed-text"
    ollama_query_model: str = "qwen2:7b"
    ollama_summarize_model: str = "qwen2:7b"

    # Whisper
    whisper_host: str = "http://whisper:8080"
    whisper_model: str = "base"

    # Telegram
    telegram_bot_token: str = ""
    telegram_allowed_users: str = ""

    # Slack
    slack_webhook_url: str = ""
    slack_signing_secret: str = ""

    # Email
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_pass: str = ""
    email_from: str = ""
    email_to: str = ""

    # Digest
    digest_daily_cron: str = "0 8 * * *"
    digest_weekly_cron: str = "0 8 * * 1"



settings = Settings()
