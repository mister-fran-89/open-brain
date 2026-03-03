import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.fixture
def temp_vault():
    with tempfile.TemporaryDirectory() as tmpdir:
        vault_path = Path(tmpdir) / "vault"
        vault_path.mkdir()
        for cat in ["people", "projects", "ideas", "admin", "_inbox", "_index"]:
            (vault_path / cat).mkdir()
        yield vault_path


@pytest.mark.asyncio
async def test_capture_text(temp_vault):
    from src.core.capture import CaptureService
    from src.core.models import Category, ClassificationResult
    from src.storage import MarkdownVault, MetadataIndex
    from src.ai import OllamaProvider

    vault = MarkdownVault(temp_vault)
    index = MetadataIndex(temp_vault / "_index" / "brain.db")
    await index.initialize()

    mock_provider = MagicMock(spec=OllamaProvider)
    mock_provider.classify = AsyncMock(
        return_value=ClassificationResult(
            category=Category.PERSON,
            title="Alice Chen",
            metadata={"organization": "Acme"},
            tags=["contact"],
            confidence=0.9,
        )
    )
    mock_provider.embed = AsyncMock(return_value=[0.1] * 384)

    service = CaptureService(vault=vault, index=index, ai_provider=mock_provider)

    item = await service.capture("Met Alice Chen from Acme Corp", source="cli")

    assert item.title == "Alice Chen"
    assert item.category == Category.PERSON
    assert item.source == "cli"

    # Verify saved to vault
    loaded = await vault.load(item.id)
    assert loaded is not None
    assert loaded.title == "Alice Chen"

    # Verify indexed
    indexed = await index.get(item.id)
    assert indexed is not None

    await index.close()


@pytest.mark.asyncio
async def test_capture_low_confidence_goes_to_inbox(temp_vault):
    from src.core.capture import CaptureService
    from src.core.models import Category, ClassificationResult
    from src.storage import MarkdownVault, MetadataIndex
    from src.ai import OllamaProvider

    vault = MarkdownVault(temp_vault)
    index = MetadataIndex(temp_vault / "_index" / "brain.db")
    await index.initialize()

    mock_provider = MagicMock(spec=OllamaProvider)
    mock_provider.classify = AsyncMock(
        return_value=ClassificationResult(
            category=Category.UNKNOWN,
            title="Ambiguous Note",
            metadata={},
            tags=[],
            confidence=0.4,
        )
    )
    mock_provider.embed = AsyncMock(return_value=[0.1] * 384)

    service = CaptureService(vault=vault, index=index, ai_provider=mock_provider)

    item = await service.capture("Something unclear", source="telegram")

    assert item.category == Category.UNKNOWN
    assert item.confidence == 0.4

    await index.close()
