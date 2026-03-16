import io
import wave
from unittest.mock import AsyncMock, patch

import pytest

from app.core.audio import (
    VOICE_AGENT,
    VOICE_CALLER,
    generate_demo_conversation_mp3,
    generate_demo_conversation_mp3_async,
    generate_demo_wav,
)

# ==============================================================
# generate_demo_wav
# ==============================================================


def test_generate_demo_wav_returns_bytes() -> None:
    result = generate_demo_wav(duration_seconds=1)
    assert isinstance(result, bytes)
    assert len(result) > 0


def test_generate_demo_wav_is_valid_wav() -> None:
    result = generate_demo_wav(duration_seconds=2)
    buf = io.BytesIO(result)
    with wave.open(buf, "rb") as wav:
        assert wav.getnchannels() == 1
        assert wav.getsampwidth() == 2
        assert wav.getframerate() == 16000
        assert wav.getnframes() == 16000 * 2  # 2 seconds at 16kHz


def test_generate_demo_wav_custom_duration() -> None:
    result_1s = generate_demo_wav(duration_seconds=1)
    result_5s = generate_demo_wav(duration_seconds=5)
    assert len(result_5s) > len(result_1s)


def test_generate_demo_wav_zero_duration() -> None:
    result = generate_demo_wav(duration_seconds=0)
    assert isinstance(result, bytes)
    buf = io.BytesIO(result)
    with wave.open(buf, "rb") as wav:
        assert wav.getnframes() == 0


def test_generate_demo_wav_starts_with_riff() -> None:
    result = generate_demo_wav(duration_seconds=1)
    assert result[:4] == b"RIFF"


def test_generate_demo_wav_is_deterministic() -> None:
    """Same duration should produce identical output (seeded random)."""
    result1 = generate_demo_wav(duration_seconds=2)
    result2 = generate_demo_wav(duration_seconds=2)
    assert result1 == result2


def test_generate_demo_wav_default_params() -> None:
    result = generate_demo_wav()
    buf = io.BytesIO(result)
    with wave.open(buf, "rb") as wav:
        assert wav.getnframes() == 16000 * 5  # default 5 seconds
        assert wav.getframerate() == 16000


def test_generate_demo_wav_custom_sample_rate() -> None:
    result = generate_demo_wav(duration_seconds=1, sample_rate=8000)
    buf = io.BytesIO(result)
    with wave.open(buf, "rb") as wav:
        assert wav.getframerate() == 8000
        assert wav.getnframes() == 8000


# ==============================================================
# Voice constants
# ==============================================================


def test_voice_constants() -> None:
    assert VOICE_AGENT != VOICE_CALLER
    assert "Neural" in VOICE_AGENT
    assert "Neural" in VOICE_CALLER
    assert VOICE_AGENT.startswith("en-US-")
    assert VOICE_CALLER.startswith("en-US-")


# ==============================================================
# generate_demo_conversation_mp3_async
# ==============================================================


@pytest.mark.asyncio
async def test_async_empty_lines_returns_wav_fallback() -> None:
    result = await generate_demo_conversation_mp3_async([])
    assert isinstance(result, bytes)
    assert result[:4] == b"RIFF"


@pytest.mark.asyncio
async def test_async_strips_objective_achieved() -> None:
    fake_mp3 = b"\xff\xfb\x90\x00" + b"\x00" * 50

    with patch("app.core.audio._synthesize_line", new_callable=AsyncMock, return_value=fake_mp3) as mock_synth:
        await generate_demo_conversation_mp3_async([
            ("Agent", "Thank you! [OBJECTIVE_ACHIEVED]"),
        ])
        mock_synth.assert_called_once_with("Thank you!", VOICE_AGENT)


@pytest.mark.asyncio
async def test_async_strips_objective_failed() -> None:
    fake_mp3 = b"\xff\xfb\x90\x00" + b"\x00" * 50

    with patch("app.core.audio._synthesize_line", new_callable=AsyncMock, return_value=fake_mp3) as mock_synth:
        await generate_demo_conversation_mp3_async([
            ("Agent", "I could not complete the task. [OBJECTIVE_FAILED]"),
        ])
        mock_synth.assert_called_once_with("I could not complete the task.", VOICE_AGENT)


@pytest.mark.asyncio
async def test_async_strips_both_markers() -> None:
    fake_mp3 = b"\xff\xfb\x90\x00" + b"\x00" * 50

    with patch("app.core.audio._synthesize_line", new_callable=AsyncMock, return_value=fake_mp3) as mock_synth:
        await generate_demo_conversation_mp3_async([
            ("Agent", "[OBJECTIVE_ACHIEVED] [OBJECTIVE_FAILED]"),
        ])
        # Both markers stripped → empty text → skipped entirely
        mock_synth.assert_not_called()


@pytest.mark.asyncio
async def test_async_uses_agent_voice_for_agent() -> None:
    fake_mp3 = b"\xff\xfb\x90\x00" + b"\x00" * 50

    with patch("app.core.audio._synthesize_line", new_callable=AsyncMock, return_value=fake_mp3) as mock_synth:
        await generate_demo_conversation_mp3_async([("Agent", "Hello")])
        mock_synth.assert_called_once_with("Hello", VOICE_AGENT)


@pytest.mark.asyncio
async def test_async_uses_caller_voice_for_interlocutor() -> None:
    fake_mp3 = b"\xff\xfb\x90\x00" + b"\x00" * 50

    with patch("app.core.audio._synthesize_line", new_callable=AsyncMock, return_value=fake_mp3) as mock_synth:
        await generate_demo_conversation_mp3_async([("Caller", "Hi")])
        mock_synth.assert_called_once_with("Hi", VOICE_CALLER)


@pytest.mark.asyncio
async def test_async_uses_caller_voice_for_non_agent_speaker() -> None:
    """Any speaker that is not 'agent' (case-insensitive) should use VOICE_CALLER."""
    fake_mp3 = b"\xff\xfb\x90\x00" + b"\x00" * 50

    with patch("app.core.audio._synthesize_line", new_callable=AsyncMock, return_value=fake_mp3) as mock_synth:
        await generate_demo_conversation_mp3_async([("Receptionist", "Welcome")])
        mock_synth.assert_called_once_with("Welcome", VOICE_CALLER)


@pytest.mark.asyncio
async def test_async_agent_case_insensitive() -> None:
    fake_mp3 = b"\xff\xfb\x90\x00" + b"\x00" * 50

    with patch("app.core.audio._synthesize_line", new_callable=AsyncMock, return_value=fake_mp3) as mock_synth:
        await generate_demo_conversation_mp3_async([("AGENT", "Test")])
        mock_synth.assert_called_once_with("Test", VOICE_AGENT)


@pytest.mark.asyncio
async def test_async_multiple_lines_different_voices() -> None:
    fake_mp3 = b"\xff\xfb\x90\x00" + b"\x00" * 50

    with patch("app.core.audio._synthesize_line", new_callable=AsyncMock, return_value=fake_mp3) as mock_synth:
        await generate_demo_conversation_mp3_async([
            ("Agent", "Hello"),
            ("Caller", "Hi"),
            ("Agent", "How are you?"),
        ])
        calls = mock_synth.call_args_list
        assert len(calls) == 3
        assert calls[0].args[1] == VOICE_AGENT
        assert calls[1].args[1] == VOICE_CALLER
        assert calls[2].args[1] == VOICE_AGENT


@pytest.mark.asyncio
async def test_async_concatenates_mp3_parts() -> None:
    part1 = b"\xff\xfb\x90\x00" + b"\x01" * 20
    part2 = b"\xff\xfb\x90\x00" + b"\x02" * 30

    call_count = 0

    async def mock_synthesize(text: str, voice: str) -> bytes:
        nonlocal call_count
        call_count += 1
        return part1 if call_count == 1 else part2

    with patch("app.core.audio._synthesize_line", side_effect=mock_synthesize):
        result = await generate_demo_conversation_mp3_async([
            ("Agent", "First"),
            ("Caller", "Second"),
        ])

    assert result == part1 + part2


@pytest.mark.asyncio
async def test_async_skips_empty_text_lines() -> None:
    fake_mp3 = b"\xff\xfb\x90\x00" + b"\x00" * 50

    with patch("app.core.audio._synthesize_line", new_callable=AsyncMock, return_value=fake_mp3) as mock_synth:
        await generate_demo_conversation_mp3_async([
            ("Agent", "Hello"),
            ("Caller", ""),
            ("Agent", "  "),
            ("Caller", "Goodbye"),
        ])
        # Only "Hello" and "Goodbye" should be synthesized
        assert mock_synth.call_count == 2


@pytest.mark.asyncio
async def test_async_skips_marker_only_lines() -> None:
    result = await generate_demo_conversation_mp3_async([
        ("Agent", "[OBJECTIVE_ACHIEVED]"),
        ("Caller", ""),
    ])
    assert result[:4] == b"RIFF"  # WAV fallback


@pytest.mark.asyncio
async def test_async_handles_tts_failure_gracefully() -> None:
    """If TTS fails for all lines, should fall back to WAV."""
    with patch("app.core.audio._synthesize_line", new_callable=AsyncMock, side_effect=Exception("TTS error")):
        result = await generate_demo_conversation_mp3_async([
            ("Agent", "Hello"),
            ("Caller", "Hi"),
        ])
    assert result[:4] == b"RIFF"


@pytest.mark.asyncio
async def test_async_handles_partial_tts_failure() -> None:
    """If TTS fails for some lines, should still return MP3 from successful ones."""
    fake_mp3 = b"\xff\xfb\x90\x00" + b"\x00" * 50
    call_count = 0

    async def mock_synthesize(text: str, voice: str) -> bytes:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("TTS error")
        return fake_mp3

    with patch("app.core.audio._synthesize_line", side_effect=mock_synthesize):
        result = await generate_demo_conversation_mp3_async([
            ("Agent", "Hello"),
            ("Caller", "Hi"),
        ])

    assert result == fake_mp3  # Only second line succeeded
    assert not result[:4].startswith(b"RIFF")


@pytest.mark.asyncio
async def test_async_skips_empty_tts_output() -> None:
    """If TTS returns empty bytes, should skip that line."""
    with patch("app.core.audio._synthesize_line", new_callable=AsyncMock, return_value=b""):
        result = await generate_demo_conversation_mp3_async([
            ("Agent", "Hello"),
        ])
    assert result[:4] == b"RIFF"  # WAV fallback


@pytest.mark.asyncio
async def test_async_edge_tts_not_installed() -> None:
    """When edge-tts import fails, should fall back to WAV."""
    with patch.dict("sys.modules", {"edge_tts": None}):
        result = await generate_demo_conversation_mp3_async([
            ("Agent", "Hello"),
        ])
    assert isinstance(result, bytes)
    # Falls back to WAV since import fails
    assert result[:4] == b"RIFF"


# ==============================================================
# generate_demo_conversation_mp3 (sync wrapper)
# ==============================================================


def test_sync_wrapper_returns_bytes() -> None:
    result = generate_demo_conversation_mp3([])
    assert isinstance(result, bytes)
    assert result[:4] == b"RIFF"  # empty lines → WAV fallback


def test_sync_wrapper_with_mock_tts() -> None:
    fake_mp3 = b"\xff\xfb\x90\x00" + b"\x00" * 50

    with patch("app.core.audio._synthesize_line", new_callable=AsyncMock, return_value=fake_mp3):
        result = generate_demo_conversation_mp3([("Agent", "Hello")])
    assert result == fake_mp3
