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
