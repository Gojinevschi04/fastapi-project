from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.calls.models import CallSession
from app.modules.calls.repository import CallSessionRepository, LogLineRepository
from app.modules.tasks.models import Task
from app.modules.tasks.repository import TaskRepository
from app.modules.tasks.schema import TaskStatus
from app.modules.templates.models import DialogTemplate
from app.modules.templates.repository import TemplateRepository
from app.modules.users.repository import UserRepository


def _make_manager(
    task_repo: MagicMock,
    template_repo: MagicMock,
    session_repo: MagicMock,
    log_repo: MagicMock,
) -> "CallManager":  # noqa: F821
    user_repo = MagicMock(spec=UserRepository)
    from app.integrations.call_manager import CallManager

    manager = CallManager(
        task_repository=task_repo,
        template_repository=template_repo,
        call_session_repository=session_repo,
        log_line_repository=log_repo,
        user_repository=user_repo,
    )
    manager._post_call = MagicMock()
    manager._post_call.process = AsyncMock()
    return manager


@pytest.mark.asyncio
async def test_execute_task_success(mock_task: Task, mock_template: DialogTemplate) -> None:
    mock_task_repo = MagicMock(spec=TaskRepository)
    mock_task_repo.get_by_id = AsyncMock(return_value=mock_task)
    mock_task_repo.update = AsyncMock(return_value=mock_task)

    mock_template_repo = MagicMock(spec=TemplateRepository)
    mock_template_repo.get_by_id = AsyncMock(return_value=mock_template)

    mock_session = CallSession(id=1, task_id=1, start_time=datetime.now())
    mock_session_repo = MagicMock(spec=CallSessionRepository)
    mock_session_repo.create = AsyncMock(return_value=mock_session)
    mock_session_repo.update = AsyncMock(return_value=mock_session)

    mock_log_repo = MagicMock(spec=LogLineRepository)
    mock_log_repo.create_many = AsyncMock(return_value=[])

    with patch("app.integrations.call_manager.TwilioAdapter") as mock_twilio, \
         patch("app.integrations.call_manager.OpenAIAdapter") as mock_openai, \
         patch("app.integrations.call_manager.PostCallProcessor"):
        mock_voice = MagicMock()
        mock_voice.initiate_call = AsyncMock(return_value="CA123")
        mock_voice.hangup = AsyncMock()
        mock_voice.get_recording_url = AsyncMock(return_value="https://example.com/rec.wav")
        mock_twilio.return_value = mock_voice

        mock_llm = MagicMock()
        mock_llm.generate_response = AsyncMock(
            side_effect=[
                "Hello, I'd like to make an appointment. [OBJECTIVE_ACHIEVED]",
                "Call summary: appointment confirmed.",
            ]
        )
        mock_llm.synthesize = AsyncMock(return_value=b"audio")
        mock_openai.return_value = mock_llm

        manager = _make_manager(mock_task_repo, mock_template_repo, mock_session_repo, mock_log_repo)
        result = await manager.execute_task(1, user_id=1)

        assert result.status == TaskStatus.COMPLETED
        assert result.summary is not None
        mock_voice.initiate_call.assert_called_once()
        mock_voice.hangup.assert_called_once()
        manager._post_call.process.assert_called_once_with(result)


@pytest.mark.asyncio
async def test_execute_task_not_found() -> None:
    mock_task_repo = MagicMock(spec=TaskRepository)
    mock_task_repo.get_by_id = AsyncMock(return_value=None)
    mock_template_repo = MagicMock(spec=TemplateRepository)
    mock_session_repo = MagicMock(spec=CallSessionRepository)
    mock_log_repo = MagicMock(spec=LogLineRepository)

    with patch("app.integrations.call_manager.TwilioAdapter"), \
         patch("app.integrations.call_manager.OpenAIAdapter"), \
         patch("app.integrations.call_manager.PostCallProcessor"):
        manager = _make_manager(mock_task_repo, mock_template_repo, mock_session_repo, mock_log_repo)
        with pytest.raises(ValueError, match="not found"):
            await manager.execute_task(999, user_id=1)


@pytest.mark.asyncio
async def test_execute_task_call_failure(mock_task: Task, mock_template: DialogTemplate) -> None:
    mock_task_repo = MagicMock(spec=TaskRepository)
    mock_task_repo.get_by_id = AsyncMock(return_value=mock_task)
    mock_task_repo.update = AsyncMock(return_value=mock_task)

    mock_template_repo = MagicMock(spec=TemplateRepository)
    mock_template_repo.get_by_id = AsyncMock(return_value=mock_template)

    mock_session = CallSession(id=1, task_id=1, start_time=datetime.now())
    mock_session_repo = MagicMock(spec=CallSessionRepository)
    mock_session_repo.create = AsyncMock(return_value=mock_session)

    mock_log_repo = MagicMock(spec=LogLineRepository)
    mock_log_repo.create_many = AsyncMock(return_value=[])

    with patch("app.integrations.call_manager.TwilioAdapter") as mock_twilio, \
         patch("app.integrations.call_manager.OpenAIAdapter") as mock_openai, \
         patch("app.integrations.call_manager.PostCallProcessor"):
        mock_voice = MagicMock()
        mock_voice.initiate_call = AsyncMock(side_effect=Exception("Connection failed"))
        mock_twilio.return_value = mock_voice

        mock_llm = MagicMock()
        mock_llm.generate_response = AsyncMock(return_value="Hello")
        mock_llm.synthesize = AsyncMock(return_value=b"audio")
        mock_openai.return_value = mock_llm

        manager = _make_manager(mock_task_repo, mock_template_repo, mock_session_repo, mock_log_repo)
        result = await manager.execute_task(1, user_id=1)

        assert result.status == TaskStatus.FAILED
        assert "Connection failed" in result.error_reason
        manager._post_call.process.assert_called_once()


@pytest.mark.asyncio
async def test_build_system_prompt() -> None:
    with patch("app.integrations.call_manager.TwilioAdapter"), \
         patch("app.integrations.call_manager.OpenAIAdapter"), \
         patch("app.integrations.call_manager.PostCallProcessor"):
        mock_task_repo = MagicMock(spec=TaskRepository)
        mock_template_repo = MagicMock(spec=TemplateRepository)
        mock_session_repo = MagicMock(spec=CallSessionRepository)
        mock_log_repo = MagicMock(spec=LogLineRepository)

        manager = _make_manager(mock_task_repo, mock_template_repo, mock_session_repo, mock_log_repo)

        prompt = manager._build_system_prompt(
            "Book an appointment",
            {"preferred_date": "March 20", "doctor_name": "Dr. Smith"},
        )

        assert "Book an appointment" in prompt
        assert "March 20" in prompt
        assert "Dr. Smith" in prompt
        assert "OBJECTIVE_ACHIEVED" in prompt


@pytest.mark.asyncio
async def test_is_conversation_complete() -> None:
    with patch("app.integrations.call_manager.TwilioAdapter"), \
         patch("app.integrations.call_manager.OpenAIAdapter"), \
         patch("app.integrations.call_manager.PostCallProcessor"):
        mock_task_repo = MagicMock(spec=TaskRepository)
        mock_template_repo = MagicMock(spec=TemplateRepository)
        mock_session_repo = MagicMock(spec=CallSessionRepository)
        mock_log_repo = MagicMock(spec=LogLineRepository)

        manager = _make_manager(mock_task_repo, mock_template_repo, mock_session_repo, mock_log_repo)

        assert manager._is_conversation_complete("Great, confirmed! [OBJECTIVE_ACHIEVED]") is True
        assert manager._is_conversation_complete("Sorry, no availability. [OBJECTIVE_FAILED]") is True
        assert manager._is_conversation_complete("When would you prefer?") is False
