import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime


@pytest.mark.asyncio
async def test_generate_digest_endpoint():
    from src.main import app
    from src.core.models import Item, Category
    from src.core.digest import Digest
    from src.api.deps import get_digest_service

    mock_digest = Digest(
        content="## Daily Summary\n\nYou captured 2 items today.",
        items=[
            Item(id="1", category=Category.PERSON, title="Alice", content="", source="cli"),
        ],
        period="daily",
        generated_at=datetime.now(),
        start_date=datetime.now(),
        end_date=datetime.now(),
    )

    # Create mock service
    mock_service = MagicMock()
    mock_service.index = MagicMock()
    mock_service.index.initialize = AsyncMock()
    mock_service.index.close = AsyncMock()
    mock_service.generate_daily = AsyncMock(return_value=mock_digest)

    # Override FastAPI dependency
    def mock_get_digest_service():
        return mock_service

    app.dependency_overrides[get_digest_service] = mock_get_digest_service

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/digest", json={"period": "daily"})

        assert response.status_code == 200
        data = response.json()
        assert data["period"] == "daily"
        assert "Summary" in data["content"] or len(data["content"]) > 0
    finally:
        app.dependency_overrides.clear()
