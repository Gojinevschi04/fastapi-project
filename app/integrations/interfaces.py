from abc import ABC, abstractmethod


class IVoiceProvider(ABC):
    @abstractmethod
    async def initiate_call(self, to_phone: str, callback_url: str) -> str:
        """Start a phone call. Returns provider call SID/ID."""

    @abstractmethod
    async def hangup(self, call_sid: str) -> None:
        """Terminate an active call."""

    @abstractmethod
    async def get_call_status(self, call_sid: str) -> str:
        """Get current call status from provider."""

    @abstractmethod
    async def get_recording_url(self, call_sid: str) -> str | None:
        """Get recording URL for a completed call."""

    @abstractmethod
    async def play_audio(self, call_sid: str, audio_bytes: bytes) -> None:
        """Stream synthesized audio to an active call via TwiML update."""

    @abstractmethod
    async def listen(self, call_sid: str, timeout: int = 10) -> bytes:
        """Capture audio from the interlocutor via Twilio Gather. Returns raw audio bytes."""

    @abstractmethod
    async def get_recording_audio(self, recording_url: str) -> bytes:
        """Download recording audio bytes from provider."""


class ILLMProvider(ABC):
    @abstractmethod
    async def transcribe(self, audio_data: bytes) -> str:
        """Speech-to-text: convert audio bytes to text."""

    @abstractmethod
    async def generate_response(self, conversation_history: list[dict[str, str]], system_prompt: str) -> str:
        """NLU + response generation: analyze intent and produce agent reply text."""

    @abstractmethod
    async def synthesize(self, text: str) -> bytes:
        """Text-to-speech: convert text to audio bytes."""

    @abstractmethod
    async def detect_intent(self, text: str) -> str | None:
        """Extract intent from interlocutor text. Returns intent label or None."""
