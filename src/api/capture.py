from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import TYPE_CHECKING

from src.api.deps import get_capture_service

if TYPE_CHECKING:
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
    service=Depends(get_capture_service),
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
