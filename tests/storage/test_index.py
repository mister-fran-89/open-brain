import pytest
import tempfile
from pathlib import Path
from datetime import datetime


@pytest.fixture
def temp_db():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "brain.db"


@pytest.mark.asyncio
async def test_index_add_and_get(temp_db):
    from src.storage.index import MetadataIndex
    from src.core.models import Item, Category

    index = MetadataIndex(temp_db)
    await index.initialize()

    item = Item(
        id="test-item-1",
        category=Category.PERSON,
        title="Alice Chen",
        content="Met Alice at the conference.",
        metadata={"organization": "Acme"},
        tags=["client"],
        confidence=0.9,
        source="cli",
    )

    await index.add(item)
    result = await index.get("test-item-1")

    assert result is not None
    assert result["title"] == "Alice Chen"
    assert result["category"] == "person"

    await index.close()


@pytest.mark.asyncio
async def test_index_search_text(temp_db):
    from src.storage.index import MetadataIndex
    from src.core.models import Item, Category

    index = MetadataIndex(temp_db)
    await index.initialize()

    item1 = Item(
        id="item-1",
        category=Category.PERSON,
        title="Alice Chen",
        content="Met Alice at the design conference in Berlin.",
        source="cli",
    )
    item2 = Item(
        id="item-2",
        category=Category.PROJECT,
        title="Website Redesign",
        content="Working on the new website layout.",
        source="cli",
    )

    await index.add(item1)
    await index.add(item2)

    results = await index.search_text("conference")
    assert len(results) == 1
    assert results[0]["id"] == "item-1"

    results = await index.search_text("website")
    assert len(results) == 1
    assert results[0]["id"] == "item-2"

    await index.close()


@pytest.mark.asyncio
async def test_index_filter_by_category(temp_db):
    from src.storage.index import MetadataIndex
    from src.core.models import Item, Category

    index = MetadataIndex(temp_db)
    await index.initialize()

    await index.add(Item(id="p1", category=Category.PERSON, title="Alice", content="", source="cli"))
    await index.add(Item(id="p2", category=Category.PERSON, title="Bob", content="", source="cli"))
    await index.add(Item(id="proj1", category=Category.PROJECT, title="Project X", content="", source="cli"))

    people = await index.filter(category=Category.PERSON)
    assert len(people) == 2

    projects = await index.filter(category=Category.PROJECT)
    assert len(projects) == 1

    await index.close()


@pytest.mark.asyncio
async def test_index_delete(temp_db):
    from src.storage.index import MetadataIndex
    from src.core.models import Item, Category

    index = MetadataIndex(temp_db)
    await index.initialize()

    item = Item(id="to-delete", category=Category.IDEA, title="Bad Idea", content="", source="cli")
    await index.add(item)

    result = await index.get("to-delete")
    assert result is not None

    await index.delete("to-delete")

    result = await index.get("to-delete")
    assert result is None

    await index.close()
