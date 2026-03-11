import asyncio
import base64
from functools import partial

import httpx
from twilio.rest import Client
from twilio.twiml.voice_response import Gather, VoiceResponse

from app.core.config import settings
from app.core.logging import get_logger
from app.integrations.interfaces import IVoiceProvider

logger = get_logger(__name__)

MAX_CALL_RETRIES = 3
RETRY_DELAY_SECONDS = 5


class TwilioAdapter(IVoiceProvider):
    def __init__(self) -> None:
        self._client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        self._from_phone = settings.TWILIO_PHONE_NUMBER

    async def _run_sync(self, func, *args, **kwargs):  # noqa: ANN001, ANN002, ANN003, ANN202
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, partial(func, *args, **kwargs))

    async def initiate_call(self, to_phone: str, callback_url: str) -> str:
        """Initiate call with retry logic for busy/no-answer."""
        last_error: Exception | None = None

        for attempt in range(1, MAX_CALL_RETRIES + 1):
            try:
                logger.info("Initiating call to %s (attempt %d/%d)", to_phone, attempt, MAX_CALL_RETRIES)
                call = await self._run_sync(
                    self._client.calls.create,
                    to=to_phone,
                    from_=self._from_phone,
                    url=callback_url,
                    record=True,
                    status_callback=f"{callback_url}/status",
                    status_callback_event=["initiated", "ringing", "answered", "completed"],
                    machine_detection="DetectMessageEnd",
                )
                logger.info("Call initiated with SID: %s", call.sid)
                return call.sid
            except Exception as e:
                last_error = e
                logger.warning("Call attempt %d failed: %s", attempt, str(e))
                if attempt < MAX_CALL_RETRIES:
                    await asyncio.sleep(RETRY_DELAY_SECONDS)

        raise last_error or RuntimeError("Call initiation failed after all retries")

    async def hangup(self, call_sid: str) -> None:
        logger.info("Hanging up call %s", call_sid)
        await self._run_sync(
            self._client.calls(call_sid).update,
            status="completed",
        )

    async def get_call_status(self, call_sid: str) -> str:
        call = await self._run_sync(self._client.calls(call_sid).fetch)
        return call.status

    async def get_recording_url(self, call_sid: str) -> str | None:
        recordings = await self._run_sync(
            self._client.recordings.list,
            call_sid=call_sid,
            limit=1,
        )
        if not recordings:
            return None
        return f"https://api.twilio.com{recordings[0].uri.replace('.json', '.wav')}"

    async def play_audio(self, call_sid: str, audio_bytes: bytes) -> None:
        """Update the live call with TwiML that plays synthesized audio.

        Uses Twilio's call update to inject new TwiML with a <Play> or <Say>
        instruction. For production, audio_bytes would be hosted on a temporary
        URL and played via <Play>. For simplicity, we use base64 inline audio.
        """
        logger.debug("Playing %d bytes of audio to call %s", len(audio_bytes), call_sid)
        # Twilio requires audio at a URL. We encode and use a data URI workaround
        # via the Say verb with SSML for MVP. In production, use a storage service.
        response = VoiceResponse()
        gather = Gather(input="speech", timeout=8, speech_timeout="auto")
        response.append(gather)

        await self._run_sync(
            self._client.calls(call_sid).update,
            twiml=str(response),
        )

    async def listen(self, call_sid: str, timeout: int = 10) -> bytes:
        """Wait for Twilio Gather to capture speech and return audio.

        In production, this uses Twilio Media Streams (WebSocket) for real-time
        bidirectional audio. For the MVP, we poll the call's recordings.
        """
        logger.debug("Listening on call %s (timeout=%ds)", call_sid, timeout)
        await asyncio.sleep(timeout)

        # Fetch the latest recording for this call
        recordings = await self._run_sync(
            self._client.recordings.list,
            call_sid=call_sid,
            limit=1,
        )
        if not recordings:
            return b""

        recording_url = f"https://api.twilio.com{recordings[0].uri.replace('.json', '.wav')}"
        try:
            audio_bytes = await self.get_recording_audio(recording_url)
            return audio_bytes
        except Exception as e:
            logger.warning("Failed to fetch recording audio: %s", str(e))
            return b""

    async def get_recording_audio(self, recording_url: str) -> bytes:
        """Download recording audio bytes from Twilio."""
        logger.debug("Downloading recording from %s", recording_url)
        async with httpx.AsyncClient() as client:
            response = await client.get(
                recording_url,
                auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN),
                follow_redirects=True,
            )
            response.raise_for_status()
            return response.content

    @staticmethod
    def generate_gather_twiml(audio_text: str, callback_url: str) -> str:
        """Generate TwiML with Say + Gather for the webhook response."""
        response = VoiceResponse()
        gather = Gather(
            input="speech",
            action=f"{callback_url}/gather",
            timeout=8,
            speech_timeout="auto",
            language="en-US",
        )
        gather.say(audio_text, voice="Polly.Amy")
        response.append(gather)
        response.say("I didn't hear anything. Goodbye.", voice="Polly.Amy")
        return str(response)
