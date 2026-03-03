from datetime import datetime
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class Category(str, Enum):
    PERSON = "person"
    PROJECT = "project"
    IDEA = "idea"
    ADMIN = "admin"
    UNKNOWN = "unknown"


class Item(BaseModel):
    id: str
    category: Category
    title: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    confidence: float = 1.0
    source: str = "unknown"
    captured: datetime = Field(default_factory=datetime.now)
    updated: datetime | None = None

    def to_frontmatter(self) -> dict[str, Any]:
        """Convert to YAML frontmatter dict."""
        fm = {
            "id": self.id,
            "type": self.category.value,
            "title": self.title,
            "tags": self.tags,
            "confidence": self.confidence,
            "captured": self.captured.isoformat(),
            "source": self.source,
        }
        if self.updated:
            fm["updated"] = self.updated.isoformat()
        # Flatten metadata into frontmatter
        fm.update(self.metadata)
        return fm

    @classmethod
    def from_frontmatter(cls, frontmatter: dict[str, Any], content: str) -> "Item":
        """Create Item from YAML frontmatter and content."""
        # Extract known fields
        known_fields = {
            "id", "type", "title", "tags", "confidence",
            "captured", "source", "updated"
        }
        metadata = {k: v for k, v in frontmatter.items() if k not in known_fields}

        captured = frontmatter.get("captured")
        if isinstance(captured, str):
            captured = datetime.fromisoformat(captured)
        elif captured is None:
            captured = datetime.now()

        updated = frontmatter.get("updated")
        if isinstance(updated, str):
            updated = datetime.fromisoformat(updated)

        return cls(
            id=frontmatter["id"],
            category=Category(frontmatter.get("type", "unknown")),
            title=frontmatter.get("title", "Untitled"),
            content=content,
            metadata=metadata,
            tags=frontmatter.get("tags", []),
            confidence=frontmatter.get("confidence", 1.0),
            source=frontmatter.get("source", "unknown"),
            captured=captured,
            updated=updated,
        )


class ClassificationResult(BaseModel):
    category: Category
    title: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    confidence: float

    @property
    def is_confident(self) -> bool:
        """Returns True if confidence is above threshold (0.7)."""
        return self.confidence >= 0.7
