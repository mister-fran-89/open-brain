import pytest
from unittest.mock import AsyncMock, patch, MagicMock


def test_classification_result_model():
    from src.core.models import ClassificationResult, Category

    result = ClassificationResult(
        category=Category.PERSON,
        title="John Doe",
        metadata={"organization": "Test Corp"},
        tags=["contact"],
        confidence=0.85,
    )
    assert result.is_confident


@pytest.mark.asyncio
async def test_ollama_provider_classify():
    from src.ai.ollama import OllamaProvider
    from src.core.models import Category

    provider = OllamaProvider(host="http://localhost:11434")

    # Mock the HTTP call
    mock_response = {
        "message": {
            "content": '{"category": "person", "title": "Alice Chen", "metadata": {"organization": "Acme"}, "tags": ["contact"], "confidence": 0.9}'
        }
    }

    with patch.object(provider, "_chat", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = mock_response["message"]["content"]
        result = await provider.classify("Met Alice Chen from Acme Corp today")

    assert result.category == Category.PERSON
    assert result.title == "Alice Chen"
    assert result.confidence == 0.9


@pytest.mark.asyncio
async def test_ollama_provider_embed():
    from src.ai.ollama import OllamaProvider

    provider = OllamaProvider(host="http://localhost:11434")

    mock_embedding = [0.1] * 384  # nomic-embed-text dimension

    with patch.object(provider, "_embed", new_callable=AsyncMock) as mock_embed:
        mock_embed.return_value = mock_embedding
        result = await provider.embed("Test text for embedding")

    assert len(result) == 384
    assert result[0] == 0.1
