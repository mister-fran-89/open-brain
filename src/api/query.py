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
                    content=item.content,
                    tags=item.tags,
                    confidence=item.confidence,
                )
                for item in items
            ],
            count=len(items),
        )
    finally:
        await service.index.close()
