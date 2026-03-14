from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_twilio_call_callback(client: AsyncClient) -> None:
    response = await client.post(
        "/webhooks/calls/1",
        data={"CallSid": "CA123", "CallStatus": "answered"},
    )
    assert response.status_code == 200
    assert "application/xml" in response.headers["content-type"]
    assert "<Response>" in response.text
    assert "<Say" in response.text


@pytest.mark.asyncio
async def test_twilio_status_callback_completed(client: AsyncClient) -> None:
    with patch("app.modules.calls.repository.CallSessionRepository.get_by_task_id") as mock_get:
        mock_session = MagicMock()
        mock_session.duration = None
        mock_get.return_value = mock_session

        with patch("app.modules.calls.repository.CallSessionRepository.update") as mock_update:
            mock_update.return_value = mock_session

            response = await client.post(
                "/webhooks/calls/1/status",
                data={"CallSid": "CA123", "CallStatus": "completed", "CallDuration": "45"},
            )
            assert response.status_code == 200
            assert mock_session.duration == 45


@pytest.mark.asyncio
async def test_twilio_status_callback_failed(client: AsyncClient) -> None:
    with patch("app.modules.calls.repository.CallSessionRepository.get_by_task_id") as mock_get:
        mock_session = MagicMock()
        mock_get.return_value = mock_session

        with patch("app.modules.calls.repository.CallSessionRepository.update") as mock_update:
            mock_update.return_value = mock_session

            response = await client.post(
                "/webhooks/calls/1/status",
                data={"CallSid": "CA123", "CallStatus": "failed", "CallDuration": "0"},
            )
            assert response.status_code == 200
            assert mock_session.duration == 0


@pytest.mark.asyncio
async def test_twilio_recording_callback(client: AsyncClient) -> None:
    with patch("app.modules.calls.repository.CallSessionRepository.get_by_task_id") as mock_get:
        mock_session = MagicMock()
        mock_get.return_value = mock_session

        with patch("app.modules.calls.repository.CallSessionRepository.update") as mock_update:
            mock_update.return_value = mock_session

            response = await client.post(
                "/webhooks/calls/1/recording",
                data={"RecordingUrl": "https://api.twilio.com/rec/123.wav", "RecordingDuration": "30"},
            )
            assert response.status_code == 200
            assert mock_session.recording_uri == "https://api.twilio.com/rec/123.wav"


@pytest.mark.asyncio
async def test_twilio_status_callback_no_session(client: AsyncClient) -> None:
    with patch("app.modules.calls.repository.CallSessionRepository.get_by_task_id") as mock_get:
        mock_get.return_value = None
        response = await client.post(
            "/webhooks/calls/999/status",
            data={"CallSid": "CA123", "CallStatus": "completed", "CallDuration": "10"},
        )
        assert response.status_code == 200  # gracefully handles missing session
