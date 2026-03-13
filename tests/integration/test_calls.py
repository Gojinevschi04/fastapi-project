from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient

from app.modules.calls.exceptions import CallSessionNotFoundError
from app.modules.calls.schema import CallSessionResponse, LogLineResponse, TranscriptResponse
from app.modules.tasks.exceptions import TaskNotFoundError


@pytest.mark.asyncio
async def test_get_transcript(authenticated_client: AsyncClient) -> None:
    with patch("app.modules.calls.service.CallService.get_transcript") as mock_get:
        mock_get.return_value = TranscriptResponse(
            session=CallSessionResponse(
                id=1,
                task_id=1,
                start_time="2026-01-01T00:00:00",
                duration=120,
                recording_uri="https://example.com/rec.wav",
                created_at="2026-01-01T00:00:00",
                updated_at="2026-01-01T00:00:00",
            ),
            lines=[
                LogLineResponse(
                    id=1,
                    session_id=1,
                    timestamp="2026-01-01T00:00:00",
                    speaker="agent",
                    text="Hello",
                    detected_intent=None,
                ),
                LogLineResponse(
                    id=2,
                    session_id=1,
                    timestamp="2026-01-01T00:00:01",
                    speaker="interlocutor",
                    text="Hi there",
                    detected_intent="greeting",
                ),
            ],
        )
        response = await authenticated_client.get("/tasks/1/transcript")
        assert response.status_code == 200
        data = response.json()
        assert len(data["lines"]) == 2
        assert data["session"]["duration"] == 120


@pytest.mark.asyncio
async def test_get_transcript_task_not_found(authenticated_client: AsyncClient) -> None:
    with patch("app.modules.calls.service.CallService.get_transcript") as mock_get:
        mock_get.side_effect = TaskNotFoundError("Not found")
        response = await authenticated_client.get("/tasks/999/transcript")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_transcript_no_session(authenticated_client: AsyncClient) -> None:
    with patch("app.modules.calls.service.CallService.get_transcript") as mock_get:
        mock_get.side_effect = CallSessionNotFoundError("No session")
        response = await authenticated_client.get("/tasks/1/transcript")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_call_session(authenticated_client: AsyncClient) -> None:
    with patch("app.modules.calls.service.CallService.get_session_by_task") as mock_get:
        mock_session = MagicMock()
        mock_session.id = 1
        mock_session.task_id = 1
        mock_session.start_time = "2026-01-01T00:00:00"
        mock_session.duration = 120
        mock_session.recording_uri = "https://example.com/rec.wav"
        mock_session.created_at = "2026-01-01T00:00:00"
        mock_session.updated_at = "2026-01-01T00:00:00"
        mock_get.return_value = mock_session

        response = await authenticated_client.get("/tasks/1/session")
        assert response.status_code == 200
        assert response.json()["duration"] == 120


@pytest.mark.asyncio
async def test_get_call_session_not_found(authenticated_client: AsyncClient) -> None:
    with patch("app.modules.calls.service.CallService.get_session_by_task") as mock_get:
        mock_get.side_effect = TaskNotFoundError("Not found")
        response = await authenticated_client.get("/tasks/999/session")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_call_session_no_session(authenticated_client: AsyncClient) -> None:
    with patch("app.modules.calls.service.CallService.get_session_by_task") as mock_get:
        mock_get.side_effect = CallSessionNotFoundError("No session")
        response = await authenticated_client.get("/tasks/1/session")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_transcript_unauthenticated(client: AsyncClient) -> None:
    response = await client.get("/tasks/1/transcript")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_call_session_unauthenticated(client: AsyncClient) -> None:
    response = await client.get("/tasks/1/session")
    assert response.status_code == 401


# --- Recording download ---


@pytest.mark.asyncio
async def test_download_recording(authenticated_client: AsyncClient) -> None:
    with patch("app.modules.calls.service.CallService.get_recording_audio") as mock_get:
        mock_get.return_value = b"RIFF" + b"\x00" * 100  # fake WAV bytes
        response = await authenticated_client.get("/tasks/1/recording")
        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/wav"
        assert "inline" in response.headers["content-disposition"]


@pytest.mark.asyncio
async def test_download_recording_as_attachment(authenticated_client: AsyncClient) -> None:
    with patch("app.modules.calls.service.CallService.get_recording_audio") as mock_get:
        mock_get.return_value = b"RIFF" + b"\x00" * 100
        response = await authenticated_client.get("/tasks/1/recording?download=true")
        assert response.status_code == 200
        assert "attachment" in response.headers["content-disposition"]
        assert "recording_task_1.wav" in response.headers["content-disposition"]


@pytest.mark.asyncio
async def test_download_recording_not_found(authenticated_client: AsyncClient) -> None:
    with patch("app.modules.calls.service.CallService.get_recording_audio") as mock_get:
        mock_get.side_effect = TaskNotFoundError("Not found")
        response = await authenticated_client.get("/tasks/999/recording")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_download_recording_no_session(authenticated_client: AsyncClient) -> None:
    with patch("app.modules.calls.service.CallService.get_recording_audio") as mock_get:
        mock_get.side_effect = CallSessionNotFoundError("No session")
        response = await authenticated_client.get("/tasks/1/recording")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_download_recording_no_uri(authenticated_client: AsyncClient) -> None:
    with patch("app.modules.calls.service.CallService.get_recording_audio") as mock_get:
        mock_get.side_effect = ValueError("No recording available")
        response = await authenticated_client.get("/tasks/1/recording")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_download_recording_unauthenticated(client: AsyncClient) -> None:
    response = await client.get("/tasks/1/recording")
    assert response.status_code == 401
