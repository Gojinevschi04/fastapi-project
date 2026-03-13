"""Utility to generate a simple WAV audio file for demo/testing."""

import struct
import wave
import io
import math


def generate_demo_wav(duration_seconds: int = 5, sample_rate: int = 16000) -> bytes:
    """Generate a simple sine wave WAV file for demo purposes.

    Creates a short audio clip with a gentle tone that sounds like
    a phone line — useful when real Twilio recordings aren't available.
    """
    buf = io.BytesIO()

    with wave.open(buf, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)

        frequency = 440  # Hz (A4 note)
        amplitude = 8000  # moderate volume

        frames = []
        for i in range(sample_rate * duration_seconds):
            # Gentle sine wave with fade in/out
            t = i / sample_rate
            fade = min(t / 0.5, 1.0) * min((duration_seconds - t) / 0.5, 1.0)
            value = int(amplitude * fade * math.sin(2 * math.pi * frequency * t))
            frames.append(struct.pack("<h", max(-32768, min(32767, value))))

        wav.writeframes(b"".join(frames))

    return buf.getvalue()
