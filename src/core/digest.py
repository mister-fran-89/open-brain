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
