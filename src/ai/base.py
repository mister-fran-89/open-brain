from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.models import ClassificationResult, Item


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    @abstractmethod
    async def classify(self, text: str) -> "ClassificationResult":
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
    async def summarize(self, items: list["Item"]) -> str:
        """Generate summary/digest from items."""
        pass
