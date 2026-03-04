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
        preprocess_provider: AIProvider = None,
    ):
        self.vault = vault
        self.index = index
        self.ai_provider = ai_provider
        self.vector_store = vector_store
        self.preprocess_provider = preprocess_provider

    async def capture(
        self,
        text: str,
        source: str = "unknown",
        category_override: Optional[str] = None,
    ) -> Item:
        """Preprocess, classify, and store a captured thought."""
        raw_text = text.strip()

        # Preprocess: clean, correct, synthesise — preserve meaning
        if self.preprocess_provider:
            clean_text = await self.preprocess_provider.preprocess(raw_text)
        else:
            clean_text = raw_text

        # Classify the clean version
        classification = await self.ai_provider.classify(clean_text)

        # Create item — clean text is content, raw input preserved in metadata
        item = Item(
            id=generate_id(),
            category=classification.category,
            title=classification.title,
            content=clean_text,
            metadata={**classification.metadata, "raw_input": raw_text},
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
