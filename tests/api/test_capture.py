import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock


@pytest.mark.asyncio
async def test_capture_text_endpoint():
    from src.main import app
    from src.core.models import Item, Category
    from src.api.deps import get_capture_service

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

    # Create mock service
    mock_service = MagicMock()
    mock_service.capture = AsyncMock(return_value=mock_item)
    mock_service.index = MagicMock()
    mock_service.index.initialize = AsyncMock()
    mock_service.index.close = AsyncMock()

    # Override FastAPI dependency
    def mock_get_capture_service():
        return mock_service

    app.dependency_overrides[get_capture_service] = mock_get_capture_service

    try:
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
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_capture_requires_text():
    from src.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/capture", json={})

    assert response.status_code == 422  # Validation error
