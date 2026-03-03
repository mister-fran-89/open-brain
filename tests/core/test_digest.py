import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
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
async def test_generate_daily_digest(temp_vault):
    from src.core.digest import DigestService
    from src.core.models import Item, Category
    from src.storage import MarkdownVault, MetadataIndex
    from src.ai import OllamaProvider

    vault = MarkdownVault(temp_vault)
    index = MetadataIndex(temp_vault / "_index" / "brain.db")
    await index.initialize()

    # Add items from "today"
    now = datetime.now()
    item1 = Item(
        id="today-1",
        category=Category.PERSON,
        title="Alice Chen",
        content="Met Alice today",
        source="cli",
        captured=now,
    )
    item2 = Item(
        id="today-2",
        category=Category.PROJECT,
        title="Project Update",
        content="Made progress on project",
        source="cli",
        captured=now,
    )
    await vault.save(item1)
    await vault.save(item2)
    await index.add(item1)
    await index.add(item2)

    mock_provider = MagicMock(spec=OllamaProvider)
    mock_provider.summarize = AsyncMock(
        return_value="## Daily Digest\n\n- Met Alice Chen\n- Made progress on project"
    )

    service = DigestService(
        vault=vault,
        index=index,
        ai_provider=mock_provider,
    )

    digest = await service.generate_daily()

    assert "Daily Digest" in digest.content or "Alice" in digest.content
    assert len(digest.items) == 2
    assert digest.period == "daily"

    await index.close()


@pytest.mark.asyncio
async def test_digest_filters_by_date(temp_vault):
    from src.core.digest import DigestService
    from src.core.models import Item, Category
    from src.storage import MarkdownVault, MetadataIndex
    from src.ai import OllamaProvider

    vault = MarkdownVault(temp_vault)
    index = MetadataIndex(temp_vault / "_index" / "brain.db")
    await index.initialize()

    now = datetime.now()
    yesterday = now - timedelta(days=1)
    last_week = now - timedelta(days=7)

    # Item from today
    today_item = Item(
        id="today",
        category=Category.IDEA,
        title="Today's Idea",
        content="Fresh idea",
        source="cli",
        captured=now,
    )
    # Item from last week (should not appear in daily)
    old_item = Item(
        id="old",
        category=Category.IDEA,
        title="Old Idea",
        content="Old idea",
        source="cli",
        captured=last_week,
    )

    await vault.save(today_item)
    await vault.save(old_item)
    await index.add(today_item)
    await index.add(old_item)

    mock_provider = MagicMock(spec=OllamaProvider)
    mock_provider.summarize = AsyncMock(return_value="Summary")

    service = DigestService(vault=vault, index=index, ai_provider=mock_provider)

    digest = await service.generate_daily()

    # Should only include today's item
    assert len(digest.items) == 1
    assert digest.items[0].id == "today"

    await index.close()
