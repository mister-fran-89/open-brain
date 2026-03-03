import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock


@pytest.mark.asyncio
async def test_query_endpoint():
    from src.main import app
    from src.core.models import Item, Category
    from src.core.query import QueryResult
    from src.api.deps import get_query_service

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

    # Create mock service
    mock_service = MagicMock()
    mock_service.index = MagicMock()
    mock_service.index.initialize = AsyncMock()
    mock_service.index.close = AsyncMock()
    mock_service.query = AsyncMock(return_value=mock_result)

    # Override FastAPI dependency
    def mock_get_query_service():
        return mock_service

    app.dependency_overrides[get_query_service] = mock_get_query_service

    try:
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
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_search_endpoint():
    from src.main import app
    from src.core.models import Item, Category
    from src.api.deps import get_query_service

    mock_items = [
        Item(id="p1", category=Category.PERSON, title="Alice", content="", source="cli"),
        Item(id="p2", category=Category.PERSON, title="Bob", content="", source="cli"),
    ]

    # Create mock service
    mock_service = MagicMock()
    mock_service.index = MagicMock()
    mock_service.index.initialize = AsyncMock()
    mock_service.index.close = AsyncMock()
    mock_service.search = AsyncMock(return_value=mock_items)

    # Override FastAPI dependency
    def mock_get_query_service():
        return mock_service

    app.dependency_overrides[get_query_service] = mock_get_query_service

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/search?category=person")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
    finally:
        app.dependency_overrides.clear()
