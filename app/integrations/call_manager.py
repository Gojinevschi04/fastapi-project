from datetime import datetime
from typing import Annotated

from fastapi import Depends

from app.core.logging import get_logger
from app.integrations.interfaces import ILLMProvider, IVoiceProvider
from app.integrations.openai_adapter import OpenAIAdapter
from app.integrations.twilio_adapter import TwilioAdapter
from app.modules.calls.models import CallSession, LogLine
from app.modules.calls.repository import CallSessionRepository, LogLineRepository
from app.modules.calls.schema import Speaker
from app.modules.notifications.post_call import PostCallProcessor
from app.modules.tasks.models import Task
from app.modules.tasks.repository import TaskRepository
from app.modules.tasks.schema import TaskStatus
from app.modules.templates.repository import TemplateRepository
from app.modules.users.repository import UserRepository

logger = get_logger(__name__)

MAX_DIALOG_TURNS = 10
MAX_RETRY_ON_NOISE = 3


class CallManager:
    def __init__(
        self,
        task_repository: Annotated[TaskRepository, Depends(TaskRepository)],
        template_repository: Annotated[TemplateRepository, Depends(TemplateRepository)],
        call_session_repository: Annotated[CallSessionRepository, Depends(CallSessionRepository)],
        log_line_repository: Annotated[LogLineRepository, Depends(LogLineRepository)],
        user_repository: Annotated[UserRepository, Depends(UserRepository)],
    ) -> None:
        self.task_repository = task_repository
        self.template_repository = template_repository
        self.call_session_repository = call_session_repository
        self.log_line_repository = log_line_repository
        self.user_repository = user_repository
        self._voice: IVoiceProvider = TwilioAdapter()
        self._llm: ILLMProvider = OpenAIAdapter()
        self._post_call = PostCallProcessor(
            task_repository=task_repository,
            user_repository=user_repository,
            call_session_repository=call_session_repository,
            log_line_repository=log_line_repository,
        )

    async def execute_task(self, task_id: int, user_id: int) -> Task:
        task = await self.task_repository.get_by_id(task_id, user_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        template = await self.template_repository.get_by_id(task.template_id)
        if not template:
            raise ValueError(f"Template {task.template_id} not found")

        task.status = TaskStatus.IN_PROGRESS
        await self.task_repository.update(task)
        logger.info("Executing task %d: calling %s", task.id, task.target_phone)

        call_session = CallSession(task_id=task.id, start_time=datetime.now())
        call_session = await self.call_session_repository.create(call_session)
        log_lines: list[LogLine] = []

        try:
            system_prompt = self._build_system_prompt(template.base_script, task.slot_data)

            call_sid = await self._voice.initiate_call(
                to_phone=task.target_phone,
                callback_url=f"{self._get_callback_base()}/webhooks/calls/{task.id}",
            )
            logger.info("Call SID: %s for task %d", call_sid, task.id)

            conversation_history: list[dict[str, str]] = []
            noise_retries = 0

            opening = await self._llm.generate_response(conversation_history, system_prompt)
            conversation_history.append({"role": "assistant", "content": opening})
            log_lines.append(self._create_log_line(call_session.id, Speaker.AGENT, opening))

            await self._llm.synthesize(opening)

            for _turn in range(MAX_DIALOG_TURNS):
                interlocutor_text = await self._simulate_listen(call_sid)

                if not interlocutor_text or interlocutor_text.strip() == "":
                    noise_retries += 1
                    if noise_retries >= MAX_RETRY_ON_NOISE:
                        log_lines.append(
                            self._create_log_line(call_session.id, Speaker.AGENT, "[Max noise retries reached]")
                        )
                        break
                    apology = "I'm sorry, I didn't catch that. Could you please repeat?"
                    conversation_history.append({"role": "assistant", "content": apology})
                    log_lines.append(self._create_log_line(call_session.id, Speaker.AGENT, apology))
                    continue

                noise_retries = 0
                conversation_history.append({"role": "user", "content": interlocutor_text})
                log_lines.append(self._create_log_line(call_session.id, Speaker.INTERLOCUTOR, interlocutor_text))

                agent_reply = await self._llm.generate_response(conversation_history, system_prompt)
                conversation_history.append({"role": "assistant", "content": agent_reply})
                log_lines.append(self._create_log_line(call_session.id, Speaker.AGENT, agent_reply))

                if self._is_conversation_complete(agent_reply):
                    break

            await self._voice.hangup(call_sid)

            call_session.duration = int((datetime.now() - call_session.start_time).total_seconds())
            call_session.recording_uri = await self._voice.get_recording_url(call_sid)
            await self.call_session_repository.update(call_session)

            summary = await self._generate_summary(conversation_history)
            task.status = TaskStatus.COMPLETED
            task.summary = summary

        except Exception as e:
            logger.error("Task %d failed: %s", task.id, str(e))
            task.status = TaskStatus.FAILED
            task.error_reason = str(e)

        await self.task_repository.update(task)

        if log_lines:
            await self.log_line_repository.create_many(log_lines)

        logger.info("Task %d finished with status: %s", task.id, task.status)

        await self._post_call.process(task)

        return task

    def _build_system_prompt(self, base_script: str, slot_data: dict[str, str]) -> str:
        prompt = (
            "You are a voice assistant making a phone call on behalf of a user. "
            "Follow this script as a guide, but adapt naturally to the conversation.\n\n"
            f"Script: {base_script}\n\n"
        )
        if slot_data:
            prompt += "Key information to use:\n"
            for key, value in slot_data.items():
                prompt += f"- {key.replace('_', ' ').title()}: {value}\n"

        prompt += (
            "\nIMPORTANT: Be polite and natural. Confirm details before ending. "
            "When the objective is achieved or clearly impossible, end the conversation politely. "
            "Include [OBJECTIVE_ACHIEVED] or [OBJECTIVE_FAILED] in your final message."
        )
        return prompt

    async def _simulate_listen(self, call_sid: str) -> str:
        """Placeholder for real-time audio capture + STT.

        In production, this would capture audio from the Twilio WebSocket stream
        and pass it through STT. For now, this is a hook for the webhook-based flow.
        """
        return ""

    async def _generate_summary(self, conversation_history: list[dict[str, str]]) -> str:
        summary_prompt = (
            "Summarize this phone conversation in 2-3 sentences. "
            "Include the outcome (success/failure) and any confirmed details."
        )
        return await self._llm.generate_response(
            [{"role": "user", "content": f"Conversation:\n{self._format_history(conversation_history)}"}],
            summary_prompt,
        )

    def _format_history(self, conversation_history: list[dict[str, str]]) -> str:
        lines = []
        for msg in conversation_history:
            role = "Agent" if msg["role"] == "assistant" else "Interlocutor"
            lines.append(f"{role}: {msg['content']}")
        return "\n".join(lines)

    def _is_conversation_complete(self, agent_reply: str) -> bool:
        return "[OBJECTIVE_ACHIEVED]" in agent_reply or "[OBJECTIVE_FAILED]" in agent_reply

    def _create_log_line(self, session_id: int, speaker: Speaker, text: str) -> LogLine:
        return LogLine(
            session_id=session_id,
            timestamp=datetime.now(),
            speaker=speaker,
            text=text,
        )

    def _get_callback_base(self) -> str:
        from app.core.config import settings

        return settings.BASE_URL
