import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_rate_limit_allows_normal_traffic() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Should allow a few requests without hitting the limit
        for _ in range(5):
            response = await client.get("/health")
            assert response.status_code == 200


@pytest.mark.asyncio
async def test_rate_limit_blocks_excessive_traffic() -> None:
    # Create a fresh app instance to avoid state from other tests
    from app.core.rate_limit import RateLimitMiddleware
    from fastapi import FastAPI

    test_app = FastAPI()
    test_app.add_middleware(RateLimitMiddleware, max_requests=3)

    @test_app.get("/test")
    async def test_endpoint() -> dict:
        return {"ok": True}

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # First 3 should pass
        for _ in range(3):
            response = await client.get("/test")
            assert response.status_code == 200

        # 4th should be rate limited
        response = await client.get("/test")
        assert response.status_code == 429
        assert "Too many requests" in response.json()["detail"]
