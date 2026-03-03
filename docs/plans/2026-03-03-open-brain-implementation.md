# Open Brain Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a personal knowledge capture and retrieval system with Obsidian-compatible storage, RAG queries, and multi-channel input/output.

**Architecture:** FastAPI monolith with pluggable AI providers, SQLite metadata index, ChromaDB vector store, and async Whisper transcription. All data stored as markdown with YAML frontmatter in a NAS-mounted Obsidian vault.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy, ChromaDB, faster-whisper, python-telegram-bot, Docker Compose

---

## Phase 1: Project Scaffold & Core Storage

### Task 1: Initialize Project Structure

**Files:**
- Create: `src/__init__.py`
- Create: `src/main.py`
- Create: `src/config/__init__.py`
- Create: `src/config/settings.py`
- Create: `requirements.txt`
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `.env.example`
- Create: `.gitignore`

**Step 1: Create .gitignore**

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
.venv/
ENV/

# Environment
.env
*.local

# IDE
.idea/
.vscode/
*.swp
*.swo

# Data (local dev)
data/
vault/

# Docker
*.log
```

**Step 2: Create requirements.txt**

```txt
# Core
fastapi==0.109.2
uvicorn[standard]==0.27.1
pydantic==2.6.1
pydantic-settings==2.1.0
python-dotenv==1.0.1

# Storage
sqlalchemy==2.0.25
aiosqlite==0.19.0
chromadb==0.4.22

# AI Providers
httpx==0.26.0
openai==1.12.0
google-generativeai==0.3.2
anthropic==0.18.1

# Adapters
python-telegram-bot==21.0.1
slack-sdk==3.27.1
aiosmtplib==3.0.1
aiofiles==23.2.1

# Utilities
pyyaml==6.0.1
python-multipart==0.0.9
jinja2==3.1.3

# Testing
pytest==8.0.0
pytest-asyncio==0.23.4
pytest-cov==4.1.0
httpx==0.26.0
```

**Step 3: Create .env.example**

```bash
# Storage paths
VAULT_PATH=/vault
DATA_PATH=/data

# AI Providers (configure what you use)
OLLAMA_HOST=http://ollama:11434
GEMINI_API_KEY=
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

# AI Routing
AI_CLASSIFY_PROVIDER=ollama
AI_EMBED_PROVIDER=ollama
AI_QUERY_PROVIDER=ollama
AI_SUMMARIZE_PROVIDER=ollama

# Models
OLLAMA_CLASSIFY_MODEL=phi3:mini
OLLAMA_EMBED_MODEL=nomic-embed-text
OLLAMA_QUERY_MODEL=qwen2:7b
OLLAMA_SUMMARIZE_MODEL=qwen2:7b

# Whisper
WHISPER_HOST=http://whisper:8080
WHISPER_MODEL=base

# Telegram
TELEGRAM_BOT_TOKEN=
TELEGRAM_ALLOWED_USERS=

# Slack
SLACK_WEBHOOK_URL=
SLACK_SIGNING_SECRET=

# Email
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASS=
EMAIL_FROM=
EMAIL_TO=

# Digest Schedule (cron format)
DIGEST_DAILY_CRON=0 8 * * *
DIGEST_WEEKLY_CRON=0 8 * * 1
```

**Step 4: Create src/config/settings.py**

```python
from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path


class Settings(BaseSettings):
    # Storage
    vault_path: Path = Field(default=Path("/vault"))
    data_path: Path = Field(default=Path("/data"))

    # AI Providers
    ollama_host: str = "http://ollama:11434"
    gemini_api_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # AI Routing
    ai_classify_provider: str = "ollama"
    ai_embed_provider: str = "ollama"
    ai_query_provider: str = "ollama"
    ai_summarize_provider: str = "ollama"

    # Models
    ollama_classify_model: str = "phi3:mini"
    ollama_embed_model: str = "nomic-embed-text"
    ollama_query_model: str = "qwen2:7b"
    ollama_summarize_model: str = "qwen2:7b"

    # Whisper
    whisper_host: str = "http://whisper:8080"
    whisper_model: str = "base"

    # Telegram
    telegram_bot_token: str = ""
    telegram_allowed_users: str = ""

    # Slack
    slack_webhook_url: str = ""
    slack_signing_secret: str = ""

    # Email
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_pass: str = ""
    email_from: str = ""
    email_to: str = ""

    # Digest
    digest_daily_cron: str = "0 8 * * *"
    digest_weekly_cron: str = "0 8 * * 1"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
```

**Step 5: Create src/config/__init__.py**

```python
from .settings import settings

__all__ = ["settings"]
```

**Step 6: Create src/__init__.py**

```python
__version__ = "0.1.0"
```

**Step 7: Create src/main.py**

```python
from fastapi import FastAPI
from contextlib import asynccontextmanager

from src.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure directories exist
    settings.vault_path.mkdir(parents=True, exist_ok=True)
    settings.data_path.mkdir(parents=True, exist_ok=True)
    (settings.vault_path / "_inbox").mkdir(exist_ok=True)
    (settings.vault_path / "_index").mkdir(exist_ok=True)
    for category in ["people", "projects", "ideas", "admin"]:
        (settings.vault_path / category).mkdir(exist_ok=True)
    yield
    # Shutdown: cleanup if needed


app = FastAPI(
    title="Open Brain",
    description="Personal knowledge capture and retrieval system",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
```

**Step 8: Create Dockerfile**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY src/ ./src/
COPY cli/ ./cli/
COPY config/ ./config/

# Create non-root user
RUN useradd -m -u 1000 brain && chown -R brain:brain /app
USER brain

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Step 9: Create docker-compose.yml**

```yaml
version: "3.8"

services:
  open-brain:
    build: .
    container_name: open-brain
    ports:
      - "8000:8000"
    volumes:
      - ${VAULT_PATH:-./vault}:/vault
      - ${DATA_PATH:-./data}:/data
    env_file:
      - .env
    depends_on:
      - chromadb
    restart: unless-stopped

  chromadb:
    image: chromadb/chroma:latest
    container_name: chromadb
    ports:
      - "8002:8000"
    volumes:
      - ${DATA_PATH:-./data}/chroma:/chroma/chroma
    environment:
      - ANONYMIZED_TELEMETRY=false
    restart: unless-stopped

  whisper:
    image: fedirz/faster-whisper-server:latest-cpu
    container_name: whisper
    ports:
      - "8001:8080"
    environment:
      - WHISPER__MODEL=${WHISPER_MODEL:-base}
    restart: unless-stopped

  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    restart: unless-stopped

volumes:
  ollama_data:
```

**Step 10: Commit scaffold**

```bash
git add -A
git commit -m "feat: initialize project scaffold with Docker Compose stack

- FastAPI app with health endpoint
- Settings from environment variables
- Docker Compose with open-brain, chromadb, whisper, ollama
- Project dependencies

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 2: Domain Models

**Files:**
- Create: `src/core/__init__.py`
- Create: `src/core/models.py`
- Create: `tests/__init__.py`
- Create: `tests/core/__init__.py`
- Create: `tests/core/test_models.py`

**Step 1: Write the failing test**

```python
# tests/core/test_models.py
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/core/test_models.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.core'"

**Step 3: Create test __init__ files**

```python
# tests/__init__.py
# tests/core/__init__.py
```

**Step 4: Write minimal implementation**

```python
# src/core/__init__.py
from .models import Item, Category, ClassificationResult

__all__ = ["Item", "Category", "ClassificationResult"]
```

```python
# src/core/models.py
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
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/core/test_models.py -v`
Expected: PASS (4 tests)

**Step 6: Commit**

```bash
git add src/core/ tests/
git commit -m "feat: add core domain models (Item, Category, ClassificationResult)

- Item model with frontmatter serialization
- Category enum (person, project, idea, admin)
- ClassificationResult with confidence threshold

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 3: Markdown Vault Storage

**Files:**
- Create: `src/storage/__init__.py`
- Create: `src/storage/vault.py`
- Create: `tests/storage/__init__.py`
- Create: `tests/storage/test_vault.py`

**Step 1: Write the failing test**

```python
# tests/storage/test_vault.py
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/storage/test_vault.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.storage'"

**Step 3: Create test __init__ file**

```python
# tests/storage/__init__.py
```

**Step 4: Write minimal implementation**

```python
# src/storage/__init__.py
from .vault import MarkdownVault

__all__ = ["MarkdownVault"]
```

```python
# src/storage/vault.py
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
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/storage/test_vault.py -v`
Expected: PASS (5 tests)

**Step 6: Commit**

```bash
git add src/storage/ tests/storage/
git commit -m "feat: add MarkdownVault for Obsidian-compatible storage

- Save items as markdown with YAML frontmatter
- Load, list, delete operations
- Category-based directory organization
- In-memory index for fast lookups

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 4: SQLite Metadata Index

**Files:**
- Create: `src/storage/index.py`
- Create: `tests/storage/test_index.py`

**Step 1: Write the failing test**

```python
# tests/storage/test_index.py
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/storage/test_index.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.storage.index'"

**Step 3: Write minimal implementation**

```python
# src/storage/index.py
from pathlib import Path
from typing import Optional
import aiosqlite

from src.core.models import Item, Category


class MetadataIndex:
    """SQLite index for fast metadata queries and full-text search."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._conn: Optional[aiosqlite.Connection] = None

    async def initialize(self):
        """Create database and tables."""
        self._conn = await aiosqlite.connect(self.db_path)
        self._conn.row_factory = aiosqlite.Row

        await self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS items (
                id TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT,
                tags TEXT,
                confidence REAL DEFAULT 1.0,
                source TEXT,
                captured TEXT,
                updated TEXT,
                metadata TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_category ON items(category);
            CREATE INDEX IF NOT EXISTS idx_captured ON items(captured);

            CREATE VIRTUAL TABLE IF NOT EXISTS items_fts USING fts5(
                id,
                title,
                content,
                tags,
                content=items,
                content_rowid=rowid
            );

            CREATE TRIGGER IF NOT EXISTS items_ai AFTER INSERT ON items BEGIN
                INSERT INTO items_fts(rowid, id, title, content, tags)
                VALUES (new.rowid, new.id, new.title, new.content, new.tags);
            END;

            CREATE TRIGGER IF NOT EXISTS items_ad AFTER DELETE ON items BEGIN
                INSERT INTO items_fts(items_fts, rowid, id, title, content, tags)
                VALUES ('delete', old.rowid, old.id, old.title, old.content, old.tags);
            END;

            CREATE TRIGGER IF NOT EXISTS items_au AFTER UPDATE ON items BEGIN
                INSERT INTO items_fts(items_fts, rowid, id, title, content, tags)
                VALUES ('delete', old.rowid, old.id, old.title, old.content, old.tags);
                INSERT INTO items_fts(rowid, id, title, content, tags)
                VALUES (new.rowid, new.id, new.title, new.content, new.tags);
            END;
        """)
        await self._conn.commit()

    async def close(self):
        """Close database connection."""
        if self._conn:
            await self._conn.close()
            self._conn = None

    async def add(self, item: Item):
        """Add or update item in index."""
        import json

        await self._conn.execute(
            """
            INSERT OR REPLACE INTO items
            (id, category, title, content, tags, confidence, source, captured, updated, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item.id,
                item.category.value,
                item.title,
                item.content,
                ",".join(item.tags),
                item.confidence,
                item.source,
                item.captured.isoformat() if item.captured else None,
                item.updated.isoformat() if item.updated else None,
                json.dumps(item.metadata),
            ),
        )
        await self._conn.commit()

    async def get(self, item_id: str) -> Optional[dict]:
        """Get item by ID."""
        cursor = await self._conn.execute(
            "SELECT * FROM items WHERE id = ?", (item_id,)
        )
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None

    async def delete(self, item_id: str):
        """Delete item from index."""
        await self._conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
        await self._conn.commit()

    async def search_text(self, query: str, limit: int = 20) -> list[dict]:
        """Full-text search across items."""
        cursor = await self._conn.execute(
            """
            SELECT items.* FROM items
            JOIN items_fts ON items.id = items_fts.id
            WHERE items_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (query, limit),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def filter(
        self,
        category: Optional[Category] = None,
        tags: Optional[list[str]] = None,
        limit: int = 100,
    ) -> list[dict]:
        """Filter items by category and/or tags."""
        conditions = []
        params = []

        if category:
            conditions.append("category = ?")
            params.append(category.value)

        if tags:
            for tag in tags:
                conditions.append("tags LIKE ?")
                params.append(f"%{tag}%")

        where = " AND ".join(conditions) if conditions else "1=1"
        params.append(limit)

        cursor = await self._conn.execute(
            f"SELECT * FROM items WHERE {where} ORDER BY captured DESC LIMIT ?",
            params,
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
```

**Step 4: Update storage __init__.py**

```python
# src/storage/__init__.py
from .vault import MarkdownVault
from .index import MetadataIndex

__all__ = ["MarkdownVault", "MetadataIndex"]
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/storage/test_index.py -v`
Expected: PASS (4 tests)

**Step 6: Commit**

```bash
git add src/storage/ tests/storage/
git commit -m "feat: add SQLite MetadataIndex with full-text search

- SQLite storage for fast metadata queries
- FTS5 full-text search with triggers
- Filter by category and tags
- Complements MarkdownVault for query performance

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Phase 2: AI Provider Abstraction

### Task 5: AI Provider Interface

**Files:**
- Create: `src/ai/__init__.py`
- Create: `src/ai/base.py`
- Create: `src/ai/ollama.py`
- Create: `tests/ai/__init__.py`
- Create: `tests/ai/test_providers.py`

**Step 1: Write the failing test**

```python
# tests/ai/test_providers.py
import pytest
from unittest.mock import AsyncMock, patch


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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/ai/test_providers.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.ai'"

**Step 3: Create test __init__ file**

```python
# tests/ai/__init__.py
```

**Step 4: Write minimal implementation**

```python
# src/ai/base.py
from abc import ABC, abstractmethod
from src.core.models import ClassificationResult, Item


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    @abstractmethod
    async def classify(self, text: str) -> ClassificationResult:
        """Classify text and extract metadata."""
        pass

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Generate embedding vector for text."""
        pass

    @abstractmethod
    async def query(self, question: str, context: list[str]) -> str:
        """Answer question using provided context (RAG)."""
        pass

    @abstractmethod
    async def summarize(self, items: list[Item]) -> str:
        """Generate summary/digest from items."""
        pass
```

```python
# src/ai/ollama.py
import json
import httpx
from typing import Optional

from src.ai.base import AIProvider
from src.core.models import ClassificationResult, Category, Item
from src.config import settings


CLASSIFY_PROMPT = """Analyze the following text and classify it into one of these categories:
- person: Information about a person (contact, meeting notes, relationship details)
- project: A task, initiative, or thing with next actions
- idea: A thought, concept, or creative spark
- admin: Administrative task, appointment, reminder

Extract a title and relevant metadata based on the category.

Respond with JSON only:
{
  "category": "person|project|idea|admin",
  "title": "Short descriptive title",
  "metadata": {"key": "value pairs relevant to category"},
  "tags": ["relevant", "tags"],
  "confidence": 0.0-1.0
}

Text to classify:
"""

QUERY_PROMPT = """You are a helpful assistant answering questions about the user's personal knowledge base.
Use the provided context to answer the question. If the answer isn't in the context, say so.
Cite sources by mentioning titles when relevant.

Context:
{context}

Question: {question}

Answer:"""

SUMMARIZE_PROMPT = """Generate a concise digest of the following items. Group by category, highlight action items, and note any patterns or connections.

Items:
{items}

Digest:"""


class OllamaProvider(AIProvider):
    """Ollama-based AI provider for local inference."""

    def __init__(
        self,
        host: str = None,
        classify_model: str = None,
        embed_model: str = None,
        query_model: str = None,
        summarize_model: str = None,
    ):
        self.host = host or settings.ollama_host
        self.classify_model = classify_model or settings.ollama_classify_model
        self.embed_model = embed_model or settings.ollama_embed_model
        self.query_model = query_model or settings.ollama_query_model
        self.summarize_model = summarize_model or settings.ollama_summarize_model
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=60.0)
        return self._client

    async def _chat(self, model: str, prompt: str) -> str:
        """Send chat completion request."""
        client = await self._get_client()
        response = await client.post(
            f"{self.host}/api/chat",
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
            },
        )
        response.raise_for_status()
        return response.json()["message"]["content"]

    async def _embed(self, model: str, text: str) -> list[float]:
        """Generate embedding."""
        client = await self._get_client()
        response = await client.post(
            f"{self.host}/api/embeddings",
            json={"model": model, "prompt": text},
        )
        response.raise_for_status()
        return response.json()["embedding"]

    async def classify(self, text: str) -> ClassificationResult:
        """Classify text and extract metadata."""
        prompt = CLASSIFY_PROMPT + text
        response = await self._chat(self.classify_model, prompt)

        try:
            # Extract JSON from response (handle markdown code blocks)
            if "```" in response:
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            data = json.loads(response.strip())
        except json.JSONDecodeError:
            # Fallback for unparseable response
            data = {
                "category": "unknown",
                "title": text[:50],
                "metadata": {},
                "tags": [],
                "confidence": 0.3,
            }

        return ClassificationResult(
            category=Category(data.get("category", "unknown")),
            title=data.get("title", "Untitled"),
            metadata=data.get("metadata", {}),
            tags=data.get("tags", []),
            confidence=data.get("confidence", 0.5),
        )

    async def embed(self, text: str) -> list[float]:
        """Generate embedding vector."""
        return await self._embed(self.embed_model, text)

    async def query(self, question: str, context: list[str]) -> str:
        """Answer question using RAG context."""
        context_text = "\n\n---\n\n".join(context)
        prompt = QUERY_PROMPT.format(context=context_text, question=question)
        return await self._chat(self.query_model, prompt)

    async def summarize(self, items: list[Item]) -> str:
        """Generate digest from items."""
        items_text = "\n\n".join(
            f"[{item.category.value}] {item.title}\n{item.content}"
            for item in items
        )
        prompt = SUMMARIZE_PROMPT.format(items=items_text)
        return await self._chat(self.summarize_model, prompt)

    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
```

```python
# src/ai/__init__.py
from .base import AIProvider
from .ollama import OllamaProvider

__all__ = ["AIProvider", "OllamaProvider"]
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/ai/test_providers.py -v`
Expected: PASS (3 tests)

**Step 6: Commit**

```bash
git add src/ai/ tests/ai/
git commit -m "feat: add AI provider abstraction with Ollama implementation

- AIProvider abstract base class
- OllamaProvider for local inference
- classify, embed, query, summarize operations
- JSON extraction from LLM responses

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 6: AI Provider Factory

**Files:**
- Create: `src/ai/factory.py`
- Modify: `src/ai/__init__.py`
- Create: `tests/ai/test_factory.py`

**Step 1: Write the failing test**

```python
# tests/ai/test_factory.py
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/ai/test_factory.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.ai.factory'"

**Step 3: Write minimal implementation**

```python
# src/ai/factory.py
from typing import Optional
from functools import lru_cache

from src.ai.base import AIProvider
from src.ai.ollama import OllamaProvider
from src.config import settings


_providers: dict[str, AIProvider] = {}


def get_provider(name: str) -> AIProvider:
    """Get or create AI provider by name."""
    if name in _providers:
        return _providers[name]

    if name == "ollama":
        provider = OllamaProvider()
    # Future: add gemini, openai, claude providers
    else:
        raise ValueError(f"Unknown provider: {name}")

    _providers[name] = provider
    return provider


def get_provider_for_task(task: str) -> AIProvider:
    """Get provider configured for specific task."""
    task_to_setting = {
        "classify": settings.ai_classify_provider,
        "embed": settings.ai_embed_provider,
        "query": settings.ai_query_provider,
        "summarize": settings.ai_summarize_provider,
    }

    provider_name = task_to_setting.get(task, "ollama")
    return get_provider(provider_name)
```

**Step 4: Update ai __init__.py**

```python
# src/ai/__init__.py
from .base import AIProvider
from .ollama import OllamaProvider
from .factory import get_provider, get_provider_for_task

__all__ = ["AIProvider", "OllamaProvider", "get_provider", "get_provider_for_task"]
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/ai/test_factory.py -v`
Expected: PASS (3 tests)

**Step 6: Commit**

```bash
git add src/ai/ tests/ai/
git commit -m "feat: add AI provider factory with task-based routing

- get_provider() for direct provider access
- get_provider_for_task() for config-driven routing
- Provider caching for efficiency

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Phase 3: Core Services

### Task 7: Capture Service

**Files:**
- Create: `src/core/capture.py`
- Create: `tests/core/test_capture.py`

**Step 1: Write the failing test**

```python
# tests/core/test_capture.py
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/core/test_capture.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.core.capture'"

**Step 3: Write minimal implementation**

```python
# src/core/capture.py
from datetime import datetime
from typing import Optional
import uuid

from src.core.models import Item, ClassificationResult
from src.storage import MarkdownVault, MetadataIndex
from src.ai.base import AIProvider


def generate_id() -> str:
    """Generate unique item ID."""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    suffix = uuid.uuid4().hex[:6]
    return f"{timestamp}-{suffix}"


class CaptureService:
    """Service for capturing and classifying new items."""

    def __init__(
        self,
        vault: MarkdownVault,
        index: MetadataIndex,
        ai_provider: AIProvider,
        vector_store=None,  # Optional ChromaDB client
    ):
        self.vault = vault
        self.index = index
        self.ai_provider = ai_provider
        self.vector_store = vector_store

    async def capture(
        self,
        text: str,
        source: str = "unknown",
        category_override: Optional[str] = None,
    ) -> Item:
        """Capture text, classify it, and store."""
        # Classify
        classification = await self.ai_provider.classify(text)

        # Create item
        item = Item(
            id=generate_id(),
            category=classification.category,
            title=classification.title,
            content=text,
            metadata=classification.metadata,
            tags=classification.tags,
            confidence=classification.confidence,
            source=source,
            captured=datetime.now(),
        )

        # Save to vault (markdown)
        await self.vault.save(item)

        # Add to index (SQLite)
        await self.index.add(item)

        # Generate and store embedding (if vector store available)
        if self.vector_store:
            embedding = await self.ai_provider.embed(text)
            await self._store_embedding(item.id, embedding, item)

        return item

    async def _store_embedding(self, item_id: str, embedding: list[float], item: Item):
        """Store embedding in vector database."""
        if self.vector_store:
            self.vector_store.add(
                ids=[item_id],
                embeddings=[embedding],
                metadatas=[{
                    "title": item.title,
                    "category": item.category.value,
                    "source": item.source,
                }],
                documents=[item.content],
            )
```

**Step 4: Update core __init__.py**

```python
# src/core/__init__.py
from .models import Item, Category, ClassificationResult
from .capture import CaptureService

__all__ = ["Item", "Category", "ClassificationResult", "CaptureService"]
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/core/test_capture.py -v`
Expected: PASS (2 tests)

**Step 6: Commit**

```bash
git add src/core/ tests/core/
git commit -m "feat: add CaptureService for text classification and storage

- Classify text via AI provider
- Store as markdown in vault
- Index in SQLite for search
- Optional vector embedding storage

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 8: Query Service (RAG)

**Files:**
- Create: `src/core/query.py`
- Create: `tests/core/test_query.py`

**Step 1: Write the failing test**

```python
# tests/core/test_query.py
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/core/test_query.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.core.query'"

**Step 3: Write minimal implementation**

```python
# src/core/query.py
from dataclasses import dataclass
from typing import Optional

from src.core.models import Item, Category
from src.storage import MarkdownVault, MetadataIndex
from src.ai.base import AIProvider


@dataclass
class QueryResult:
    """Result of a natural language query."""
    answer: str
    sources: list[Item]
    confidence: float = 1.0


class QueryService:
    """Service for querying the knowledge base."""

    def __init__(
        self,
        vault: MarkdownVault,
        index: MetadataIndex,
        ai_provider: AIProvider,
        vector_store=None,
    ):
        self.vault = vault
        self.index = index
        self.ai_provider = ai_provider
        self.vector_store = vector_store

    async def query(self, question: str, limit: int = 5) -> QueryResult:
        """Answer a natural language question using RAG."""
        # Get relevant context
        if self.vector_store:
            # Vector similarity search
            context_items = await self._vector_search(question, limit)
        else:
            # Fallback to text search
            context_items = await self._text_search(question, limit)

        if not context_items:
            return QueryResult(
                answer="I don't have any relevant information to answer that question.",
                sources=[],
                confidence=0.0,
            )

        # Build context strings
        context_texts = [
            f"[{item.title}]\n{item.content}"
            for item in context_items
        ]

        # Generate answer
        answer = await self.ai_provider.query(question, context_texts)

        return QueryResult(
            answer=answer,
            sources=context_items,
        )

    async def _vector_search(self, question: str, limit: int) -> list[Item]:
        """Search using vector similarity."""
        embedding = await self.ai_provider.embed(question)
        results = self.vector_store.query(
            query_embeddings=[embedding],
            n_results=limit,
        )

        items = []
        if results and results["ids"]:
            for item_id in results["ids"][0]:
                item = await self.vault.load(item_id)
                if item:
                    items.append(item)
        return items

    async def _text_search(self, question: str, limit: int) -> list[Item]:
        """Search using full-text search."""
        # Extract key terms (simple approach)
        terms = question.lower().split()
        stop_words = {"what", "who", "where", "when", "how", "do", "i", "know", "about", "the", "a", "an", "is", "are"}
        keywords = [t for t in terms if t not in stop_words and len(t) > 2]

        items = []
        for keyword in keywords[:3]:  # Search top 3 keywords
            results = await self.index.search_text(keyword, limit=limit)
            for result in results:
                item = await self.vault.load(result["id"])
                if item and item not in items:
                    items.append(item)

        return items[:limit]

    async def search(
        self,
        category: Optional[Category] = None,
        tags: Optional[list[str]] = None,
        text: Optional[str] = None,
        limit: int = 20,
    ) -> list[Item]:
        """Structured search with filters."""
        if text:
            results = await self.index.search_text(text, limit=limit)
        else:
            results = await self.index.filter(category=category, tags=tags, limit=limit)

        items = []
        for result in results:
            item = await self.vault.load(result["id"])
            if item:
                items.append(item)

        return items
```

**Step 4: Update core __init__.py**

```python
# src/core/__init__.py
from .models import Item, Category, ClassificationResult
from .capture import CaptureService
from .query import QueryService, QueryResult

__all__ = [
    "Item", "Category", "ClassificationResult",
    "CaptureService", "QueryService", "QueryResult"
]
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/core/test_query.py -v`
Expected: PASS (2 tests)

**Step 6: Commit**

```bash
git add src/core/ tests/core/
git commit -m "feat: add QueryService with RAG and text search

- Natural language queries with context retrieval
- Vector search (ChromaDB) or text search fallback
- Structured search with category/tag filters
- QueryResult with answer and source citations

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 9: Digest Service

**Files:**
- Create: `src/core/digest.py`
- Create: `tests/core/test_digest.py`

**Step 1: Write the failing test**

```python
# tests/core/test_digest.py
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/core/test_digest.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.core.digest'"

**Step 3: Write minimal implementation**

```python
# src/core/digest.py
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from src.core.models import Item
from src.storage import MarkdownVault, MetadataIndex
from src.ai.base import AIProvider


@dataclass
class Digest:
    """Generated digest/summary."""
    content: str
    items: list[Item]
    period: str  # "daily", "weekly", "custom"
    generated_at: datetime
    start_date: datetime
    end_date: datetime


class DigestService:
    """Service for generating periodic digests."""

    def __init__(
        self,
        vault: MarkdownVault,
        index: MetadataIndex,
        ai_provider: AIProvider,
    ):
        self.vault = vault
        self.index = index
        self.ai_provider = ai_provider

    async def generate_daily(self) -> Digest:
        """Generate digest for the past 24 hours."""
        end = datetime.now()
        start = end - timedelta(days=1)
        return await self.generate(start, end, period="daily")

    async def generate_weekly(self) -> Digest:
        """Generate digest for the past 7 days."""
        end = datetime.now()
        start = end - timedelta(days=7)
        return await self.generate(start, end, period="weekly")

    async def generate(
        self,
        start: datetime,
        end: datetime,
        period: str = "custom",
    ) -> Digest:
        """Generate digest for a date range."""
        # Get all items and filter by date
        all_items = await self.vault.list_all()
        items = [
            item for item in all_items
            if start <= item.captured <= end
        ]

        if not items:
            return Digest(
                content="No items captured during this period.",
                items=[],
                period=period,
                generated_at=datetime.now(),
                start_date=start,
                end_date=end,
            )

        # Sort by category for grouping
        items.sort(key=lambda x: (x.category.value, x.captured))

        # Generate AI summary
        content = await self.ai_provider.summarize(items)

        return Digest(
            content=content,
            items=items,
            period=period,
            generated_at=datetime.now(),
            start_date=start,
            end_date=end,
        )

    def format_digest_markdown(self, digest: Digest) -> str:
        """Format digest as markdown."""
        lines = [
            f"# {digest.period.title()} Digest",
            f"*{digest.start_date.strftime('%Y-%m-%d')} to {digest.end_date.strftime('%Y-%m-%d')}*",
            "",
            digest.content,
            "",
            "---",
            "",
            "## Items Included",
            "",
        ]

        by_category = {}
        for item in digest.items:
            cat = item.category.value
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(item)

        for category, items in by_category.items():
            lines.append(f"### {category.title()}")
            for item in items:
                lines.append(f"- **{item.title}** ({item.captured.strftime('%H:%M')})")
            lines.append("")

        return "\n".join(lines)
```

**Step 4: Update core __init__.py**

```python
# src/core/__init__.py
from .models import Item, Category, ClassificationResult
from .capture import CaptureService
from .query import QueryService, QueryResult
from .digest import DigestService, Digest

__all__ = [
    "Item", "Category", "ClassificationResult",
    "CaptureService", "QueryService", "QueryResult",
    "DigestService", "Digest",
]
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/core/test_digest.py -v`
Expected: PASS (2 tests)

**Step 6: Commit**

```bash
git add src/core/ tests/core/
git commit -m "feat: add DigestService for daily/weekly summaries

- Generate digests for configurable date ranges
- AI-powered summarization of captured items
- Markdown formatting for output
- Filter items by capture date

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Phase 4: API Endpoints

### Task 10: Capture API Endpoint

**Files:**
- Create: `src/api/__init__.py`
- Create: `src/api/capture.py`
- Create: `src/api/deps.py`
- Modify: `src/main.py`
- Create: `tests/api/__init__.py`
- Create: `tests/api/test_capture.py`

**Step 1: Write the failing test**

```python
# tests/api/test_capture.py
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_capture_text_endpoint():
    from src.main import app
    from src.core.models import Item, Category, ClassificationResult

    mock_item = Item(
        id="test-123",
        category=Category.PERSON,
        title="Alice Chen",
        content="Met Alice at conference",
        metadata={"organization": "Acme"},
        tags=["contact"],
        confidence=0.9,
        source="api",
    )

    with patch("src.api.capture.get_capture_service") as mock_get_service:
        mock_service = MagicMock()
        mock_service.capture = AsyncMock(return_value=mock_item)
        mock_get_service.return_value = mock_service

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/capture",
                json={"text": "Met Alice at conference", "source": "test"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-123"
        assert data["title"] == "Alice Chen"
        assert data["category"] == "person"


@pytest.mark.asyncio
async def test_capture_requires_text():
    from src.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/capture", json={})

    assert response.status_code == 422  # Validation error
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/api/test_capture.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.api'"

**Step 3: Create test __init__ file**

```python
# tests/api/__init__.py
```

**Step 4: Write implementation**

```python
# src/api/__init__.py
```

```python
# src/api/deps.py
from functools import lru_cache
from pathlib import Path
from typing import Optional

from src.config import settings
from src.storage import MarkdownVault, MetadataIndex
from src.ai import get_provider_for_task
from src.core import CaptureService, QueryService, DigestService

# Singletons
_vault: Optional[MarkdownVault] = None
_index: Optional[MetadataIndex] = None


async def get_vault() -> MarkdownVault:
    global _vault
    if _vault is None:
        _vault = MarkdownVault(settings.vault_path)
    return _vault


async def get_index() -> MetadataIndex:
    global _index
    if _index is None:
        db_path = settings.vault_path / "_index" / "brain.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        _index = MetadataIndex(db_path)
        await _index.initialize()
    return _index


def get_capture_service() -> CaptureService:
    # Note: This is synchronous for simplicity, services are stateless
    from src.storage import MarkdownVault, MetadataIndex
    vault = MarkdownVault(settings.vault_path)
    db_path = settings.vault_path / "_index" / "brain.db"
    index = MetadataIndex(db_path)
    ai = get_provider_for_task("classify")
    return CaptureService(vault=vault, index=index, ai_provider=ai)


def get_query_service() -> QueryService:
    from src.storage import MarkdownVault, MetadataIndex
    vault = MarkdownVault(settings.vault_path)
    db_path = settings.vault_path / "_index" / "brain.db"
    index = MetadataIndex(db_path)
    ai = get_provider_for_task("query")
    return QueryService(vault=vault, index=index, ai_provider=ai)


def get_digest_service() -> DigestService:
    from src.storage import MarkdownVault, MetadataIndex
    vault = MarkdownVault(settings.vault_path)
    db_path = settings.vault_path / "_index" / "brain.db"
    index = MetadataIndex(db_path)
    ai = get_provider_for_task("summarize")
    return DigestService(vault=vault, index=index, ai_provider=ai)
```

```python
# src/api/capture.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from src.api.deps import get_capture_service
from src.core import CaptureService


router = APIRouter(prefix="/api", tags=["capture"])


class CaptureRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to capture")
    source: str = Field(default="api", description="Source of capture")


class CaptureResponse(BaseModel):
    id: str
    category: str
    title: str
    content: str
    tags: list[str]
    confidence: float
    source: str


@router.post("/capture", response_model=CaptureResponse)
async def capture_text(
    request: CaptureRequest,
    service: CaptureService = Depends(get_capture_service),
):
    """Capture and classify text."""
    # Initialize index
    await service.index.initialize()

    try:
        item = await service.capture(request.text, source=request.source)
        return CaptureResponse(
            id=item.id,
            category=item.category.value,
            title=item.title,
            content=item.content,
            tags=item.tags,
            confidence=item.confidence,
            source=item.source,
        )
    finally:
        await service.index.close()
```

**Step 5: Update main.py to include router**

```python
# src/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager

from src.config import settings
from src.api.capture import router as capture_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure directories exist
    settings.vault_path.mkdir(parents=True, exist_ok=True)
    settings.data_path.mkdir(parents=True, exist_ok=True)
    (settings.vault_path / "_inbox").mkdir(exist_ok=True)
    (settings.vault_path / "_index").mkdir(exist_ok=True)
    for category in ["people", "projects", "ideas", "admin"]:
        (settings.vault_path / category).mkdir(exist_ok=True)
    yield
    # Shutdown: cleanup if needed


app = FastAPI(
    title="Open Brain",
    description="Personal knowledge capture and retrieval system",
    version="0.1.0",
    lifespan=lifespan,
)

# Include routers
app.include_router(capture_router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
```

**Step 6: Run test to verify it passes**

Run: `pytest tests/api/test_capture.py -v`
Expected: PASS (2 tests)

**Step 7: Commit**

```bash
git add src/api/ src/main.py tests/api/
git commit -m "feat: add /api/capture endpoint

- POST /api/capture for text classification
- Dependency injection for services
- Request/response models with validation

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 11: Query API Endpoint

**Files:**
- Create: `src/api/query.py`
- Modify: `src/main.py`
- Create: `tests/api/test_query.py`

**Step 1: Write the failing test**

```python
# tests/api/test_query.py
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_query_endpoint():
    from src.main import app
    from src.core.models import Item, Category
    from src.core.query import QueryResult

    mock_item = Item(
        id="source-1",
        category=Category.PERSON,
        title="Alice Chen",
        content="Works at Acme",
        source="cli",
    )

    mock_result = QueryResult(
        answer="Alice Chen works at Acme Corp.",
        sources=[mock_item],
        confidence=0.9,
    )

    with patch("src.api.query.get_query_service") as mock_get_service:
        mock_service = MagicMock()
        mock_service.index = MagicMock()
        mock_service.index.initialize = AsyncMock()
        mock_service.index.close = AsyncMock()
        mock_service.query = AsyncMock(return_value=mock_result)
        mock_get_service.return_value = mock_service

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/query",
                json={"question": "What do I know about Alice?"}
            )

        assert response.status_code == 200
        data = response.json()
        assert "Alice" in data["answer"]
        assert len(data["sources"]) == 1


@pytest.mark.asyncio
async def test_search_endpoint():
    from src.main import app
    from src.core.models import Item, Category

    mock_items = [
        Item(id="p1", category=Category.PERSON, title="Alice", content="", source="cli"),
        Item(id="p2", category=Category.PERSON, title="Bob", content="", source="cli"),
    ]

    with patch("src.api.query.get_query_service") as mock_get_service:
        mock_service = MagicMock()
        mock_service.index = MagicMock()
        mock_service.index.initialize = AsyncMock()
        mock_service.index.close = AsyncMock()
        mock_service.search = AsyncMock(return_value=mock_items)
        mock_get_service.return_value = mock_service

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/search?category=person")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/api/test_query.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.api.query'"

**Step 3: Write implementation**

```python
# src/api/query.py
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional

from src.api.deps import get_query_service
from src.core import QueryService
from src.core.models import Category


router = APIRouter(prefix="/api", tags=["query"])


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Question to answer")
    limit: int = Field(default=5, ge=1, le=20, description="Max context items")


class SourceItem(BaseModel):
    id: str
    title: str
    category: str


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceItem]


class SearchItem(BaseModel):
    id: str
    category: str
    title: str
    content: str
    tags: list[str]
    confidence: float


class SearchResponse(BaseModel):
    items: list[SearchItem]
    count: int


@router.post("/query", response_model=QueryResponse)
async def query(
    request: QueryRequest,
    service: QueryService = Depends(get_query_service),
):
    """Answer a natural language question using RAG."""
    await service.index.initialize()

    try:
        result = await service.query(request.question, limit=request.limit)
        return QueryResponse(
            answer=result.answer,
            sources=[
                SourceItem(
                    id=item.id,
                    title=item.title,
                    category=item.category.value,
                )
                for item in result.sources
            ],
        )
    finally:
        await service.index.close()


@router.get("/search", response_model=SearchResponse)
async def search(
    category: Optional[str] = Query(None, description="Filter by category"),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    text: Optional[str] = Query(None, description="Full-text search"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
    service: QueryService = Depends(get_query_service),
):
    """Structured search with filters."""
    await service.index.initialize()

    try:
        cat = Category(category) if category else None
        tag_list = tags.split(",") if tags else None

        items = await service.search(
            category=cat,
            tags=tag_list,
            text=text,
            limit=limit,
        )

        return SearchResponse(
            items=[
                SearchItem(
                    id=item.id,
                    category=item.category.value,
                    title=item.title,
                    content=item.content[:200],  # Truncate for response
                    tags=item.tags,
                    confidence=item.confidence,
                )
                for item in items
            ],
            count=len(items),
        )
    finally:
        await service.index.close()
```

**Step 4: Update main.py**

```python
# src/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager

from src.config import settings
from src.api.capture import router as capture_router
from src.api.query import router as query_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure directories exist
    settings.vault_path.mkdir(parents=True, exist_ok=True)
    settings.data_path.mkdir(parents=True, exist_ok=True)
    (settings.vault_path / "_inbox").mkdir(exist_ok=True)
    (settings.vault_path / "_index").mkdir(exist_ok=True)
    for category in ["people", "projects", "ideas", "admin"]:
        (settings.vault_path / category).mkdir(exist_ok=True)
    yield
    # Shutdown: cleanup if needed


app = FastAPI(
    title="Open Brain",
    description="Personal knowledge capture and retrieval system",
    version="0.1.0",
    lifespan=lifespan,
)

# Include routers
app.include_router(capture_router)
app.include_router(query_router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/api/test_query.py -v`
Expected: PASS (2 tests)

**Step 6: Commit**

```bash
git add src/api/ src/main.py tests/api/
git commit -m "feat: add /api/query and /api/search endpoints

- POST /api/query for RAG-powered Q&A
- GET /api/search for structured filtering
- Support category, tags, and text filters

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 12: Digest API Endpoint

**Files:**
- Create: `src/api/digest.py`
- Modify: `src/main.py`
- Create: `tests/api/test_digest.py`

**Step 1: Write the failing test**

```python
# tests/api/test_digest.py
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


@pytest.mark.asyncio
async def test_generate_digest_endpoint():
    from src.main import app
    from src.core.models import Item, Category
    from src.core.digest import Digest

    mock_digest = Digest(
        content="## Daily Summary\n\nYou captured 2 items today.",
        items=[
            Item(id="1", category=Category.PERSON, title="Alice", content="", source="cli"),
        ],
        period="daily",
        generated_at=datetime.now(),
        start_date=datetime.now(),
        end_date=datetime.now(),
    )

    with patch("src.api.digest.get_digest_service") as mock_get_service:
        mock_service = MagicMock()
        mock_service.index = MagicMock()
        mock_service.index.initialize = AsyncMock()
        mock_service.index.close = AsyncMock()
        mock_service.generate_daily = AsyncMock(return_value=mock_digest)
        mock_get_service.return_value = mock_service

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/digest", json={"period": "daily"})

        assert response.status_code == 200
        data = response.json()
        assert data["period"] == "daily"
        assert "Summary" in data["content"] or len(data["content"]) > 0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/api/test_digest.py -v`
Expected: FAIL

**Step 3: Write implementation**

```python
# src/api/digest.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from src.api.deps import get_digest_service
from src.core import DigestService


router = APIRouter(prefix="/api", tags=["digest"])


class DigestRequest(BaseModel):
    period: str = Field(default="daily", description="daily, weekly, or custom")
    start_date: Optional[str] = Field(None, description="Start date (ISO format) for custom period")
    end_date: Optional[str] = Field(None, description="End date (ISO format) for custom period")


class DigestItem(BaseModel):
    id: str
    category: str
    title: str


class DigestResponse(BaseModel):
    content: str
    items: list[DigestItem]
    period: str
    generated_at: str
    start_date: str
    end_date: str


@router.post("/digest", response_model=DigestResponse)
async def generate_digest(
    request: DigestRequest,
    service: DigestService = Depends(get_digest_service),
):
    """Generate a digest for the specified period."""
    await service.index.initialize()

    try:
        if request.period == "daily":
            digest = await service.generate_daily()
        elif request.period == "weekly":
            digest = await service.generate_weekly()
        elif request.period == "custom" and request.start_date and request.end_date:
            start = datetime.fromisoformat(request.start_date)
            end = datetime.fromisoformat(request.end_date)
            digest = await service.generate(start, end, period="custom")
        else:
            digest = await service.generate_daily()

        return DigestResponse(
            content=digest.content,
            items=[
                DigestItem(
                    id=item.id,
                    category=item.category.value,
                    title=item.title,
                )
                for item in digest.items
            ],
            period=digest.period,
            generated_at=digest.generated_at.isoformat(),
            start_date=digest.start_date.isoformat(),
            end_date=digest.end_date.isoformat(),
        )
    finally:
        await service.index.close()
```

**Step 4: Update main.py**

```python
# src/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager

from src.config import settings
from src.api.capture import router as capture_router
from src.api.query import router as query_router
from src.api.digest import router as digest_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.vault_path.mkdir(parents=True, exist_ok=True)
    settings.data_path.mkdir(parents=True, exist_ok=True)
    (settings.vault_path / "_inbox").mkdir(exist_ok=True)
    (settings.vault_path / "_index").mkdir(exist_ok=True)
    for category in ["people", "projects", "ideas", "admin"]:
        (settings.vault_path / category).mkdir(exist_ok=True)
    yield


app = FastAPI(
    title="Open Brain",
    description="Personal knowledge capture and retrieval system",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(capture_router)
app.include_router(query_router)
app.include_router(digest_router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/api/test_digest.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add src/api/ src/main.py tests/api/
git commit -m "feat: add /api/digest endpoint

- POST /api/digest for on-demand digest generation
- Support daily, weekly, and custom date ranges

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Phase 5: CLI & Bootstrap

### Task 13: CLI Tool

**Files:**
- Create: `cli/__init__.py`
- Create: `cli/brain.py`

**Step 1: Write CLI tool**

```python
# cli/__init__.py
```

```python
# cli/brain.py
#!/usr/bin/env python3
"""Open Brain CLI - capture and query your knowledge base."""

import argparse
import asyncio
import sys
from pathlib import Path

# Add src to path for local development
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx


DEFAULT_HOST = "http://localhost:8000"


async def capture(args):
    """Capture text to the brain."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{args.host}/api/capture",
            json={"text": args.text, "source": "cli"},
            timeout=30.0,
        )

    if response.status_code == 200:
        data = response.json()
        print(f"✓ Captured: {data['title']}")
        print(f"  Category: {data['category']}")
        print(f"  Confidence: {data['confidence']:.0%}")
        print(f"  ID: {data['id']}")
    else:
        print(f"✗ Error: {response.status_code}")
        print(response.text)
        sys.exit(1)


async def query(args):
    """Query the brain."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{args.host}/api/query",
            json={"question": args.question},
            timeout=60.0,
        )

    if response.status_code == 200:
        data = response.json()
        print(data["answer"])
        if data["sources"]:
            print("\n---\nSources:")
            for source in data["sources"]:
                print(f"  - {source['title']} ({source['category']})")
    else:
        print(f"✗ Error: {response.status_code}")
        print(response.text)
        sys.exit(1)


async def search(args):
    """Search the brain."""
    params = {}
    if args.category:
        params["category"] = args.category
    if args.tags:
        params["tags"] = args.tags
    if args.text:
        params["text"] = args.text

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{args.host}/api/search",
            params=params,
            timeout=30.0,
        )

    if response.status_code == 200:
        data = response.json()
        print(f"Found {data['count']} items:\n")
        for item in data["items"]:
            print(f"[{item['category']}] {item['title']}")
            if item["content"]:
                print(f"  {item['content'][:100]}...")
            print()
    else:
        print(f"✗ Error: {response.status_code}")
        sys.exit(1)


async def digest(args):
    """Generate a digest."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{args.host}/api/digest",
            json={"period": args.period},
            timeout=60.0,
        )

    if response.status_code == 200:
        data = response.json()
        print(data["content"])
        print(f"\n---\n{len(data['items'])} items included")
    else:
        print(f"✗ Error: {response.status_code}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Open Brain - Personal Knowledge System",
        prog="brain",
    )
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help=f"API host (default: {DEFAULT_HOST})",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Capture command
    capture_parser = subparsers.add_parser("capture", help="Capture text")
    capture_parser.add_argument("text", help="Text to capture")
    capture_parser.set_defaults(func=capture)

    # Query command
    query_parser = subparsers.add_parser("query", help="Ask a question")
    query_parser.add_argument("question", help="Question to ask")
    query_parser.set_defaults(func=query)

    # Search command
    search_parser = subparsers.add_parser("search", help="Search items")
    search_parser.add_argument("--category", "-c", help="Filter by category")
    search_parser.add_argument("--tags", "-t", help="Filter by tags (comma-separated)")
    search_parser.add_argument("--text", "-q", help="Full-text search")
    search_parser.set_defaults(func=search)

    # Digest command
    digest_parser = subparsers.add_parser("digest", help="Generate digest")
    digest_parser.add_argument(
        "--period", "-p",
        default="daily",
        choices=["daily", "weekly"],
        help="Digest period",
    )
    digest_parser.set_defaults(func=digest)

    args = parser.parse_args()
    asyncio.run(args.func(args))


if __name__ == "__main__":
    main()
```

**Step 2: Commit**

```bash
git add cli/
git commit -m "feat: add brain CLI tool

- brain capture 'text' - capture and classify
- brain query 'question' - RAG-powered Q&A
- brain search --category/--tags/--text - structured search
- brain digest --period daily|weekly - generate summaries

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 14: Bootstrap Script

**Files:**
- Create: `setup.sh`

**Step 1: Write bootstrap script**

```bash
#!/bin/bash
# Open Brain Bootstrap Script
# Run on fresh Debian 12 LXC: curl -fsSL <url>/setup.sh | bash

set -e

echo "╔════════════════════════════════════════╗"
echo "║       Open Brain Setup Script          ║"
echo "╚════════════════════════════════════════╝"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    log_error "Please run as root or with sudo"
    exit 1
fi

# Update system
log_info "Updating system packages..."
apt-get update
apt-get upgrade -y

# Install dependencies
log_info "Installing dependencies..."
apt-get install -y \
    curl \
    git \
    ca-certificates \
    gnupg \
    cifs-utils

# Install Docker
log_info "Installing Docker..."
if ! command -v docker &> /dev/null; then
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg

    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
        $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
        tee /etc/apt/sources.list.d/docker.list > /dev/null

    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
else
    log_info "Docker already installed"
fi

# Create install directory
INSTALL_DIR="/opt/open-brain"
log_info "Creating installation directory: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Clone repository (or copy if local)
if [ -d ".git" ]; then
    log_info "Updating existing repository..."
    git pull
else
    log_info "Cloning repository..."
    # Replace with your actual repo URL
    git clone https://github.com/YOUR_USERNAME/open-brain.git .
fi

# Create .env from example if not exists
if [ ! -f ".env" ]; then
    log_info "Creating .env file from template..."
    cp .env.example .env
    log_warn "Please edit .env with your configuration!"
fi

# Create data directories
log_info "Creating data directories..."
mkdir -p /data
mkdir -p /vault

# Prompt for NAS mount (optional)
echo ""
log_warn "NAS Mount Configuration"
echo "If you want to mount a NAS share for the vault, add to /etc/fstab:"
echo "  //nas-ip/share /vault cifs credentials=/etc/nas-creds,uid=1000,gid=1000 0 0"
echo ""
echo "Then create /etc/nas-creds with:"
echo "  username=your_user"
echo "  password=your_pass"
echo ""

# Create brain CLI symlink
log_info "Creating brain CLI symlink..."
ln -sf "$INSTALL_DIR/cli/brain.py" /usr/local/bin/brain
chmod +x "$INSTALL_DIR/cli/brain.py"

# Summary
echo ""
echo "╔════════════════════════════════════════╗"
echo "║          Setup Complete!               ║"
echo "╚════════════════════════════════════════╝"
echo ""
log_info "Next steps:"
echo "  1. Edit /opt/open-brain/.env with your configuration"
echo "  2. (Optional) Configure NAS mount for /vault"
echo "  3. Start services: cd /opt/open-brain && docker compose up -d"
echo "  4. Pull Ollama models: docker exec ollama ollama pull phi3:mini"
echo "  5. Test: brain capture 'Hello world'"
echo ""
```

**Step 2: Commit**

```bash
git add setup.sh
chmod +x setup.sh
git commit -m "feat: add bootstrap setup script

- Installs Docker on Debian 12
- Clones repository to /opt/open-brain
- Creates .env from template
- Sets up brain CLI symlink
- Provides NAS mount guidance

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Phase 6: Adapters (Future Tasks)

The following tasks are defined but implementation is deferred to later iterations:

### Task 15: Telegram Bot Adapter
- Create `src/adapters/telegram.py`
- Webhook receiver for messages
- Bot commands: /capture, /query, /digest
- Send digest notifications

### Task 16: Slack Adapter
- Create `src/adapters/slack.py`
- Slash commands integration
- Webhook for notifications

### Task 17: Email Adapter
- Create `src/adapters/email.py`
- SMTP sender for digests
- IMAP receiver for capture (via n8n)

### Task 18: Whisper Integration
- Create `src/adapters/whisper.py`
- Voice file transcription endpoint
- Integration with capture flow

### Task 19: ChromaDB Vector Store
- Create `src/storage/vector.py`
- Embedding storage and retrieval
- Integration with QueryService

### Task 20: Scheduled Digests
- Add scheduler to main.py
- Cron-based digest generation
- Multi-channel delivery

---

## Summary

This plan covers the core system in 14 implementation tasks:

| Phase | Tasks | Focus |
|-------|-------|-------|
| 1 | 1-4 | Scaffold, models, storage |
| 2 | 5-6 | AI provider abstraction |
| 3 | 7-9 | Core services (capture, query, digest) |
| 4 | 10-12 | API endpoints |
| 5 | 13-14 | CLI and bootstrap |
| 6 | 15-20 | Adapters (future) |

After completing Phase 5, you'll have a working system that can:
- Capture and classify text via API/CLI
- Query knowledge base with RAG
- Generate daily/weekly digests
- Store as Obsidian-compatible markdown
- Deploy via Docker Compose on Debian LXC
