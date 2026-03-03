import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def temp_vault():
    with tempfile.TemporaryDirectory() as tmpdir:
        vault_path = Path(tmpdir) / "vault"
        vault_path.mkdir()
        for cat in ["people", "projects", "ideas", "admin", "_inbox", "_index"]:
            (vault_path / cat).mkdir()
        yield vault_path


@pytest.mark.asyncio
async def test_query_with_context(temp_vault):
    from src.core.query import QueryService
    from src.core.models import Item, Category
    from src.storage import MarkdownVault, MetadataIndex
    from src.ai import OllamaProvider

    vault = MarkdownVault(temp_vault)
    index = MetadataIndex(temp_vault / "_index" / "brain.db")
    await index.initialize()

    # Add test items
    item1 = Item(
        id="item-1",
        category=Category.PERSON,
        title="Alice Chen",
        content="Alice works at Acme Corp as a designer. Met her at the conference.",
        source="cli",
    )
    item2 = Item(
        id="item-2",
        category=Category.PROJECT,
        title="Website Redesign",
        content="Working on redesign with Alice. Due next month.",
        source="cli",
    )
    await vault.save(item1)
    await vault.save(item2)
    await index.add(item1)
    await index.add(item2)

    mock_provider = MagicMock(spec=OllamaProvider)
    mock_provider.query = AsyncMock(
        return_value="Alice Chen works at Acme Corp as a designer. You met her at a conference and are collaborating on a website redesign."
    )
    mock_provider.embed = AsyncMock(return_value=[0.1] * 384)

    service = QueryService(
        vault=vault,
        index=index,
        ai_provider=mock_provider,
        vector_store=None,  # Use text search fallback
    )

    result = await service.query("What do I know about Alice?")

    assert "Alice" in result.answer
    assert len(result.sources) > 0

    await index.close()


@pytest.mark.asyncio
async def test_query_structured_search(temp_vault):
    from src.core.query import QueryService
    from src.core.models import Item, Category
    from src.storage import MarkdownVault, MetadataIndex
    from src.ai import OllamaProvider

    vault = MarkdownVault(temp_vault)
    index = MetadataIndex(temp_vault / "_index" / "brain.db")
    await index.initialize()

    # Add test items
    for i in range(3):
        item = Item(
            id=f"person-{i}",
            category=Category.PERSON,
            title=f"Person {i}",
            content=f"Details about person {i}",
            source="cli",
        )
        await vault.save(item)
        await index.add(item)

    mock_provider = MagicMock(spec=OllamaProvider)

    service = QueryService(
        vault=vault,
        index=index,
        ai_provider=mock_provider,
    )

    results = await service.search(category=Category.PERSON)

    assert len(results) == 3

    await index.close()
