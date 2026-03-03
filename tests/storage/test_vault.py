import pytest
import tempfile
from pathlib import Path


@pytest.fixture
def temp_vault():
    with tempfile.TemporaryDirectory() as tmpdir:
        vault_path = Path(tmpdir) / "vault"
        vault_path.mkdir()
        for cat in ["people", "projects", "ideas", "admin", "_inbox"]:
            (vault_path / cat).mkdir()
        yield vault_path


@pytest.mark.asyncio
async def test_vault_save_item(temp_vault):
    from src.storage.vault import MarkdownVault
    from src.core.models import Item, Category

    vault = MarkdownVault(temp_vault)
    item = Item(
        id="20260303-143022-abc123",
        category=Category.PERSON,
        title="Alice Chen",
        content="Met Alice at the design conference.",
        metadata={"organization": "Acme Corp"},
        tags=["client"],
        confidence=0.87,
        source="cli",
    )

    path = await vault.save(item)
    assert path.exists()
    assert path.name == "alice-chen.md"
    assert path.parent.name == "people"


@pytest.mark.asyncio
async def test_vault_load_item(temp_vault):
    from src.storage.vault import MarkdownVault
    from src.core.models import Item, Category

    vault = MarkdownVault(temp_vault)
    item = Item(
        id="20260303-143022-abc123",
        category=Category.PERSON,
        title="Alice Chen",
        content="Met Alice at the design conference.",
        metadata={"organization": "Acme Corp"},
        tags=["client"],
        confidence=0.87,
        source="cli",
    )

    await vault.save(item)
    loaded = await vault.load("20260303-143022-abc123")

    assert loaded is not None
    assert loaded.title == "Alice Chen"
    assert loaded.category == Category.PERSON
    assert loaded.metadata["organization"] == "Acme Corp"


@pytest.mark.asyncio
async def test_vault_list_items(temp_vault):
    from src.storage.vault import MarkdownVault
    from src.core.models import Item, Category

    vault = MarkdownVault(temp_vault)

    item1 = Item(
        id="item-1",
        category=Category.PERSON,
        title="Alice",
        content="Person 1",
        source="cli",
    )
    item2 = Item(
        id="item-2",
        category=Category.PROJECT,
        title="Project X",
        content="A project",
        source="cli",
    )

    await vault.save(item1)
    await vault.save(item2)

    all_items = await vault.list_all()
    assert len(all_items) == 2

    people = await vault.list_by_category(Category.PERSON)
    assert len(people) == 1
    assert people[0].title == "Alice"


@pytest.mark.asyncio
async def test_vault_delete_item(temp_vault):
    from src.storage.vault import MarkdownVault
    from src.core.models import Item, Category

    vault = MarkdownVault(temp_vault)
    item = Item(
        id="to-delete",
        category=Category.IDEA,
        title="Bad Idea",
        content="Delete me",
        source="cli",
    )

    path = await vault.save(item)
    assert path.exists()

    await vault.delete("to-delete")
    assert not path.exists()

    loaded = await vault.load("to-delete")
    assert loaded is None
