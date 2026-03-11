import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "degraded")
    assert "database" in data
    assert data["version"] == "1.0.0"


@pytest.mark.asyncio
async def test_health_check_no_auth_required(client: AsyncClient) -> None:
    # Health check should work without authentication
    response = await client.get("/health")
    assert response.status_code == 200
