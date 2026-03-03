import pytest
from datetime import datetime


def test_item_creation():
    from src.core.models import Item, Category

    item = Item(
        id="20260303-143022-abc123",
        category=Category.PERSON,
        title="Alice Chen",
        content="Met Alice at the design conference.",
        metadata={"organization": "Acme Corp"},
        tags=["client", "design"],
        confidence=0.87,
        source="telegram",
    )

    assert item.id == "20260303-143022-abc123"
    assert item.category == Category.PERSON
    assert item.title == "Alice Chen"
    assert item.confidence == 0.87


def test_item_to_frontmatter():
    from src.core.models import Item, Category

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

    frontmatter = item.to_frontmatter()
    assert frontmatter["id"] == "20260303-143022-abc123"
    assert frontmatter["type"] == "person"
    assert frontmatter["title"] == "Alice Chen"
    assert "organization" in frontmatter


def test_item_from_frontmatter():
    from src.core.models import Item, Category

    frontmatter = {
        "id": "20260303-143022-abc123",
        "type": "person",
        "title": "Alice Chen",
        "tags": ["client"],
        "confidence": 0.87,
        "captured": "2026-03-03T14:30:22",
        "source": "cli",
        "organization": "Acme Corp",
    }
    content = "Met Alice at the design conference."

    item = Item.from_frontmatter(frontmatter, content)
    assert item.category == Category.PERSON
    assert item.metadata["organization"] == "Acme Corp"


def test_classification_result():
    from src.core.models import ClassificationResult, Category

    result = ClassificationResult(
        category=Category.PROJECT,
        title="Website Redesign",
        metadata={"status": "active", "next_action": "Review mockups"},
        tags=["work", "design"],
        confidence=0.92,
    )

    assert result.category == Category.PROJECT
    assert result.confidence == 0.92
    assert result.is_confident  # > 0.7 threshold
