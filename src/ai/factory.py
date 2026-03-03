from typing import Optional
from functools import lru_cache

from src.ai.base import AIProvider
from src.ai.ollama import OllamaProvider
from src.config import settings


_providers: dict[str, AIProvider] = {}


def get_provider(name: str) -> AIProvider:
    """Get or create AI provider by name."""
    if name in _providers:
        return _providers[name]

    if name == "ollama":
        provider = OllamaProvider()
    # Future: add gemini, openai, claude providers
    else:
        raise ValueError(f"Unknown provider: {name}")

    _providers[name] = provider
    return provider


def get_provider_for_task(task: str) -> AIProvider:
    """Get provider configured for specific task."""
    task_to_setting = {
        "classify": settings.ai_classify_provider,
        "embed": settings.ai_embed_provider,
        "query": settings.ai_query_provider,
        "summarize": settings.ai_summarize_provider,
    }

    provider_name = task_to_setting.get(task, "ollama")
    return get_provider(provider_name)
