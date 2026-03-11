from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_initiate_call() -> None:
    with patch("app.integrations.twilio_adapter.Client") as mock_client_cls, \
         patch("app.integrations.twilio_adapter.settings") as mock_settings:
        mock_settings.TWILIO_ACCOUNT_SID = "test-sid"
        mock_settings.TWILIO_AUTH_TOKEN = "test-token"
        mock_settings.TWILIO_PHONE_NUMBER = "+15551234567"

        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        mock_call = MagicMock()
        mock_call.sid = "CA123456"
        mock_client.calls.create.return_value = mock_call

        from app.integrations.twilio_adapter import TwilioAdapter

        adapter = TwilioAdapter()
        # Patch _run_sync to just call the function directly
        adapter._run_sync = AsyncMock(return_value=mock_call)

        result = await adapter.initiate_call("+37312345678", "https://example.com/webhook")

        assert result == "CA123456"


@pytest.mark.asyncio
async def test_hangup() -> None:
    with patch("app.integrations.twilio_adapter.Client") as mock_client_cls, \
         patch("app.integrations.twilio_adapter.settings") as mock_settings:
        mock_settings.TWILIO_ACCOUNT_SID = "test-sid"
        mock_settings.TWILIO_AUTH_TOKEN = "test-token"
        mock_settings.TWILIO_PHONE_NUMBER = "+15551234567"

        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        from app.integrations.twilio_adapter import TwilioAdapter

        adapter = TwilioAdapter()
        adapter._run_sync = AsyncMock(return_value=None)

        await adapter.hangup("CA123456")
        adapter._run_sync.assert_called_once()


@pytest.mark.asyncio
async def test_get_call_status() -> None:
    with patch("app.integrations.twilio_adapter.Client") as mock_client_cls, \
         patch("app.integrations.twilio_adapter.settings") as mock_settings:
        mock_settings.TWILIO_ACCOUNT_SID = "test-sid"
        mock_settings.TWILIO_AUTH_TOKEN = "test-token"
        mock_settings.TWILIO_PHONE_NUMBER = "+15551234567"

        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        mock_call = MagicMock()
        mock_call.status = "completed"

        from app.integrations.twilio_adapter import TwilioAdapter

        adapter = TwilioAdapter()
        adapter._run_sync = AsyncMock(return_value=mock_call)

        result = await adapter.get_call_status("CA123456")
        assert result == "completed"


@pytest.mark.asyncio
async def test_get_recording_url() -> None:
    with patch("app.integrations.twilio_adapter.Client") as mock_client_cls, \
         patch("app.integrations.twilio_adapter.settings") as mock_settings:
        mock_settings.TWILIO_ACCOUNT_SID = "test-sid"
        mock_settings.TWILIO_AUTH_TOKEN = "test-token"
        mock_settings.TWILIO_PHONE_NUMBER = "+15551234567"

        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        mock_recording = MagicMock()
        mock_recording.uri = "/2010-04-01/Accounts/AC123/Recordings/RE123.json"

        from app.integrations.twilio_adapter import TwilioAdapter

        adapter = TwilioAdapter()
        adapter._run_sync = AsyncMock(return_value=[mock_recording])

        result = await adapter.get_recording_url("CA123456")
        assert result == "https://api.twilio.com/2010-04-01/Accounts/AC123/Recordings/RE123.wav"


@pytest.mark.asyncio
async def test_get_recording_url_none() -> None:
    with patch("app.integrations.twilio_adapter.Client") as mock_client_cls, \
         patch("app.integrations.twilio_adapter.settings") as mock_settings:
        mock_settings.TWILIO_ACCOUNT_SID = "test-sid"
        mock_settings.TWILIO_AUTH_TOKEN = "test-token"
        mock_settings.TWILIO_PHONE_NUMBER = "+15551234567"

        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        from app.integrations.twilio_adapter import TwilioAdapter

        adapter = TwilioAdapter()
        adapter._run_sync = AsyncMock(return_value=[])

        result = await adapter.get_recording_url("CA123456")
        assert result is None
