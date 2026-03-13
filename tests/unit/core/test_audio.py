import io
import wave

import pytest

from app.core.audio import generate_demo_wav


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
    # Should still be a valid WAV header
    buf = io.BytesIO(result)
    with wave.open(buf, "rb") as wav:
        assert wav.getnframes() == 0
