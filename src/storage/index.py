from pathlib import Path
from typing import Optional
import json
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
