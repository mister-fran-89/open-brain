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
        import re

        # Extract key terms (simple approach)
        terms = question.lower().split()
        stop_words = {"what", "who", "where", "when", "how", "do", "i", "know", "about", "the", "a", "an", "is", "are"}
        keywords = [t for t in terms if t not in stop_words and len(t) > 2]

        # Clean keywords for FTS5 (remove special characters)
        keywords = [re.sub(r'[^\w]', '', k) for k in keywords]
        keywords = [k for k in keywords if k]  # Remove empty strings

        items = []
        for keyword in keywords[:3]:  # Search top 3 keywords
            try:
                results = await self.index.search_text(keyword, limit=limit)
                for result in results:
                    item = await self.vault.load(result["id"])
                    if item and item not in items:
                        items.append(item)
            except Exception:
                # Skip if search fails (e.g., FTS5 syntax issues)
                continue

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
