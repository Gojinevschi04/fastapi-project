import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_submit_feedback(client: AsyncClient) -> None:
    """Feedback endpoint is public — no auth needed."""
    response = await client.post("/feedback/", json={
        "name": "Jane Doe",
        "email": "jane@example.com",
        "message": "I love this app! Very useful.",
    })
    assert response.status_code == 200
    assert "thank you" in response.json()["message"].lower()


@pytest.mark.asyncio
async def test_submit_feedback_missing_fields(client: AsyncClient) -> None:
    response = await client.post("/feedback/", json={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_submit_feedback_invalid_email(client: AsyncClient) -> None:
    response = await client.post("/feedback/", json={
        "name": "Jane",
        "email": "not-an-email",
        "message": "Great app!",
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_submit_feedback_message_too_short(client: AsyncClient) -> None:
    response = await client.post("/feedback/", json={
        "name": "Jane",
        "email": "jane@example.com",
        "message": "Hi",
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_submit_feedback_name_too_long(client: AsyncClient) -> None:
    response = await client.post("/feedback/", json={
        "name": "x" * 101,
        "email": "jane@example.com",
        "message": "This is a valid message.",
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_submit_feedback_empty_name(client: AsyncClient) -> None:
    response = await client.post("/feedback/", json={
        "name": "   ",
        "email": "jane@example.com",
        "message": "This is a valid message.",
    })
    assert response.status_code == 422
