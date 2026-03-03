import pytest
from unittest.mock import patch


def test_get_provider_ollama():
    from src.ai.factory import get_provider
    from src.ai.ollama import OllamaProvider

    provider = get_provider("ollama")
    assert isinstance(provider, OllamaProvider)


def test_get_provider_for_task():
    from src.ai.factory import get_provider_for_task
    from src.ai.ollama import OllamaProvider

    # Default config routes everything to ollama
    provider = get_provider_for_task("classify")
    assert isinstance(provider, OllamaProvider)


def test_get_provider_unknown_raises():
    from src.ai.factory import get_provider

    with pytest.raises(ValueError, match="Unknown provider"):
        get_provider("unknown_provider")
