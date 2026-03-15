"""Utility to generate a realistic-sounding demo phone call WAV file."""

import io
import math
import random
import struct
import wave


def generate_demo_wav(duration_seconds: int = 5, sample_rate: int = 16000) -> bytes:
    """Generate a WAV file that sounds like a phone call recording.

    Simulates a phone conversation with:
    - Low phone-line background hum (60Hz + harmonics)
    - Speech-like amplitude patterns (bursts of activity with pauses)
    - Subtle noise floor (like a real phone connection)
    """
    buf = io.BytesIO()
    random.seed(42)  # deterministic for consistency

    with wave.open(buf, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)

        frames = []
        total_samples = sample_rate * duration_seconds

        # Pre-generate speech pattern (alternating talk/silence segments)
        speech_segments = _generate_speech_pattern(duration_seconds)

        for i in range(total_samples):
            t = i / sample_rate

            # 1. Phone line hum (60Hz + 120Hz harmonic, very quiet)
            hum = 200 * math.sin(2 * math.pi * 60 * t)
            hum += 100 * math.sin(2 * math.pi * 120 * t)

            # 2. Background noise (subtle static)
            noise = random.gauss(0, 150)

            # 3. Speech-like signal (formant frequencies modulated by envelope)
            speech = _speech_signal(t, speech_segments)

            # Mix and fade in/out
            fade = min(t / 0.3, 1.0) * min((duration_seconds - t) / 0.3, 1.0)
            value = int(fade * (hum + noise + speech))
            value = max(-32768, min(32767, value))
            frames.append(struct.pack("<h", value))

        wav.writeframes(b"".join(frames))

    return buf.getvalue()


def _generate_speech_pattern(duration: int) -> list[tuple[float, float, bool]]:
    """Generate alternating talk/pause segments like a conversation.

    Returns list of (start_time, end_time, is_speaking).
    """
    segments = []
    t = 0.0
    speaking = True
    random.seed(42)

    while t < duration:
        if speaking:
            length = random.uniform(1.5, 4.0)  # talk for 1.5-4 seconds
        else:
            length = random.uniform(0.3, 1.5)  # pause for 0.3-1.5 seconds

        end = min(t + length, duration)
        segments.append((t, end, speaking))
        t = end
        speaking = not speaking

    return segments


def _speech_signal(t: float, segments: list[tuple[float, float, bool]]) -> float:
    """Generate a speech-like audio signal at time t.

    Uses multiple formant frequencies with amplitude modulation
    to approximate the sound of human speech over a phone line.
    """
    # Find current segment
    is_speaking = False
    for start, end, speaking in segments:
        if start <= t < end:
            is_speaking = speaking
            break

    if not is_speaking:
        return 0.0

    # Speech formants (typical phone band: 300-3400 Hz)
    amplitude = 3000

    # Amplitude modulation (syllable-like rhythm at ~4 Hz)
    syllable_env = 0.5 + 0.5 * math.sin(2 * math.pi * 3.8 * t)

    # Micro-variations (vocal fry / natural irregularity)
    micro = 0.7 + 0.3 * math.sin(2 * math.pi * 0.7 * t)

    # Formant frequencies (simplified vowel-like sounds)
    f1 = 500 + 200 * math.sin(2 * math.pi * 0.5 * t)   # first formant
    f2 = 1500 + 400 * math.sin(2 * math.pi * 0.3 * t)   # second formant
    f3 = 2500 + 200 * math.sin(2 * math.pi * 0.2 * t)   # third formant

    signal = (
        math.sin(2 * math.pi * f1 * t) * 1.0
        + math.sin(2 * math.pi * f2 * t) * 0.6
        + math.sin(2 * math.pi * f3 * t) * 0.3
    )

    # Phone band filter effect (reduce high freq perception)
    signal *= amplitude * syllable_env * micro * 0.4

    return signal
