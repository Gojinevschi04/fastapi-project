from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_transcribe() -> None:
    with patch("app.integrations.openai_adapter.AsyncOpenAI") as mock_openai, \
         patch("app.integrations.openai_adapter.settings") as mock_settings:
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_settings.OPENAI_MODEL = "gpt-4o"
        mock_settings.OPENAI_TTS_MODEL = "tts-1"
        mock_settings.OPENAI_TTS_VOICE = "alloy"
        mock_settings.OPENAI_STT_MODEL = "whisper-1"

        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_transcript = MagicMock()
        mock_transcript.text = "Hello, I'd like an appointment"
        mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_transcript)

        from app.integrations.openai_adapter import OpenAIAdapter

        adapter = OpenAIAdapter()
        result = await adapter.transcribe(b"fake audio data")

        assert result == "Hello, I'd like an appointment"
        mock_client.audio.transcriptions.create.assert_called_once()


@pytest.mark.asyncio
async def test_generate_response() -> None:
    with patch("app.integrations.openai_adapter.AsyncOpenAI") as mock_openai, \
         patch("app.integrations.openai_adapter.settings") as mock_settings:
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_settings.OPENAI_MODEL = "gpt-4o"
        mock_settings.OPENAI_TTS_MODEL = "tts-1"
        mock_settings.OPENAI_TTS_VOICE = "alloy"
        mock_settings.OPENAI_STT_MODEL = "whisper-1"

        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_choice = MagicMock()
        mock_choice.message.content = "Sure, when would you prefer?"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        from app.integrations.openai_adapter import OpenAIAdapter

        adapter = OpenAIAdapter()
        result = await adapter.generate_response(
            [{"role": "user", "content": "I need an appointment"}],
            "You are a helpful assistant",
        )

        assert result == "Sure, when would you prefer?"


@pytest.mark.asyncio
async def test_synthesize() -> None:
    with patch("app.integrations.openai_adapter.AsyncOpenAI") as mock_openai, \
         patch("app.integrations.openai_adapter.settings") as mock_settings:
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_settings.OPENAI_MODEL = "gpt-4o"
        mock_settings.OPENAI_TTS_MODEL = "tts-1"
        mock_settings.OPENAI_TTS_VOICE = "alloy"
        mock_settings.OPENAI_STT_MODEL = "whisper-1"

        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = b"fake audio bytes"
        mock_client.audio.speech.create = AsyncMock(return_value=mock_response)

        from app.integrations.openai_adapter import OpenAIAdapter

        adapter = OpenAIAdapter()
        result = await adapter.synthesize("Hello there")

        assert result == b"fake audio bytes"
        mock_client.audio.speech.create.assert_called_once()
