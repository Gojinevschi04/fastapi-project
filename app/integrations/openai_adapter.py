import io

from openai import AsyncOpenAI

from app.core.config import settings
from app.core.logging import get_logger
from app.integrations.interfaces import ILLMProvider

logger = get_logger(__name__)


class OpenAIAdapter(ILLMProvider):
    def __init__(self) -> None:
        self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self._model = settings.OPENAI_MODEL
        self._tts_model = settings.OPENAI_TTS_MODEL
        self._tts_voice = settings.OPENAI_TTS_VOICE
        self._stt_model = settings.OPENAI_STT_MODEL

    async def transcribe(self, audio_data: bytes) -> str:
        logger.debug("Transcribing %d bytes of audio", len(audio_data))
        audio_file = io.BytesIO(audio_data)
        audio_file.name = "audio.wav"

        transcript = await self._client.audio.transcriptions.create(
            model=self._stt_model,
            file=audio_file,
        )
        logger.debug("Transcription result: %s", transcript.text[:100])
        return transcript.text

    async def generate_response(self, conversation_history: list[dict[str, str]], system_prompt: str) -> str:
        logger.debug("Generating response with %d messages in history", len(conversation_history))
        messages = [{"role": "system", "content": system_prompt}, *conversation_history]

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=0.7,
            max_tokens=300,
        )
        reply = response.choices[0].message.content or ""
        logger.debug("Generated response: %s", reply[:100])
        return reply

    async def synthesize(self, text: str) -> bytes:
        logger.debug("Synthesizing speech for: %s", text[:100])
        response = await self._client.audio.speech.create(
            model=self._tts_model,
            voice=self._tts_voice,
            input=text,
        )
        audio_bytes = response.content
        logger.debug("Synthesized %d bytes of audio", len(audio_bytes))
        return audio_bytes
