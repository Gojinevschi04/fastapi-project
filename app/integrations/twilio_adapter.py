import asyncio
from functools import partial

from twilio.rest import Client

from app.core.config import settings
from app.core.logging import get_logger
from app.integrations.interfaces import IVoiceProvider

logger = get_logger(__name__)


class TwilioAdapter(IVoiceProvider):
    def __init__(self) -> None:
        self._client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        self._from_phone = settings.TWILIO_PHONE_NUMBER

    async def _run_sync(self, func, *args, **kwargs):  # noqa: ANN001, ANN002, ANN003, ANN202
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, partial(func, *args, **kwargs))

    async def initiate_call(self, to_phone: str, callback_url: str) -> str:
        logger.info("Initiating call to %s", to_phone)
        call = await self._run_sync(
            self._client.calls.create,
            to=to_phone,
            from_=self._from_phone,
            url=callback_url,
            record=True,
            status_callback=f"{callback_url}/status",
            status_callback_event=["initiated", "ringing", "answered", "completed"],
        )
        logger.info("Call initiated with SID: %s", call.sid)
        return call.sid

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
