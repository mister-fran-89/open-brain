import re
from pathlib import Path
from typing import Optional

import aiofiles
import yaml

from src.core.models import Item, Category


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text[:50].strip("-")


class MarkdownVault:
    """Markdown file storage for Items."""

    CATEGORY_DIRS = {
        Category.PERSON: "people",
        Category.PROJECT: "projects",
        Category.IDEA: "ideas",
        Category.ADMIN: "admin",
        Category.UNKNOWN: "_inbox",
    }

    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        self._index: dict[str, Path] = {}  # id -> file path

    def _get_dir(self, category: Category) -> Path:
        """Get directory for category."""
        dir_name = self.CATEGORY_DIRS.get(category, "_inbox")
        return self.vault_path / dir_name

    def _get_path(self, item: Item) -> Path:
        """Generate file path for item."""
        dir_path = self._get_dir(item.category)
        filename = f"{slugify(item.title)}.md"
        return dir_path / filename

    async def save(self, item: Item) -> Path:
        """Save item to markdown file."""
        path = self._get_path(item)
        path.parent.mkdir(parents=True, exist_ok=True)

        frontmatter = yaml.dump(
            item.to_frontmatter(),
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )

        content = f"---\n{frontmatter}---\n\n{item.content}\n"

        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            await f.write(content)

        self._index[item.id] = path
        return path

    async def load(self, item_id: str) -> Optional[Item]:
        """Load item by ID."""
        # Check index first
        if item_id in self._index:
            path = self._index[item_id]
            if path.exists():
                return await self._load_file(path)
            else:
                del self._index[item_id]

        # Scan vault for item
        for category_dir in self.CATEGORY_DIRS.values():
            dir_path = self.vault_path / category_dir
            if not dir_path.exists():
                continue
            for file_path in dir_path.glob("*.md"):
                item = await self._load_file(file_path)
                if item and item.id == item_id:
                    self._index[item_id] = file_path
                    return item

        return None

    async def _load_file(self, path: Path) -> Optional[Item]:
        """Load item from markdown file."""
        try:
            async with aiofiles.open(path, "r", encoding="utf-8") as f:
                content = await f.read()

            # Parse frontmatter
            if not content.startswith("---"):
                return None

            parts = content.split("---", 2)
            if len(parts) < 3:
                return None

            frontmatter = yaml.safe_load(parts[1])
            body = parts[2].strip()

            return Item.from_frontmatter(frontmatter, body)
        except Exception:
            return None

    async def list_all(self) -> list[Item]:
        """List all items in vault."""
        items = []
        for category_dir in self.CATEGORY_DIRS.values():
            dir_path = self.vault_path / category_dir
            if not dir_path.exists():
                continue
            for file_path in dir_path.glob("*.md"):
                item = await self._load_file(file_path)
                if item:
                    self._index[item.id] = file_path
                    items.append(item)
        return items

    async def list_by_category(self, category: Category) -> list[Item]:
        """List items by category."""
        dir_path = self._get_dir(category)
        if not dir_path.exists():
            return []

        items = []
        for file_path in dir_path.glob("*.md"):
            item = await self._load_file(file_path)
            if item:
                self._index[item.id] = file_path
                items.append(item)
        return items

    async def delete(self, item_id: str) -> bool:
        """Delete item by ID."""
        item = await self.load(item_id)
        if not item:
            return False

        path = self._index.get(item_id)
        if path and path.exists():
            path.unlink()
            del self._index[item_id]
            return True

        return False
