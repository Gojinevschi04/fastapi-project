from datetime import datetime

from app.integrations.conversation import ConversationManager
from app.modules.calls.schema import Speaker


def test_add_agent_message() -> None:
    conv = ConversationManager(max_turns=10, max_noise_retries=3)
    conv.add_agent_message("Hello!", session_id=1)

    assert len(conv.history) == 1
    assert conv.history[0] == {"role": "assistant", "content": "Hello!"}
    assert len(conv.log_lines) == 1
    assert conv.log_lines[0].speaker == Speaker.AGENT
    assert conv.log_lines[0].text == "Hello!"
    assert conv.log_lines[0].session_id == 1


def test_add_interlocutor_message() -> None:
    conv = ConversationManager(max_turns=10, max_noise_retries=3)
    conv.add_interlocutor_message("Hi there", intent="greeting", session_id=1)

    assert len(conv.history) == 1
    assert conv.history[0] == {"role": "user", "content": "Hi there"}
    assert len(conv.log_lines) == 1
    assert conv.log_lines[0].speaker == Speaker.INTERLOCUTOR
    assert conv.log_lines[0].detected_intent == "greeting"


def test_is_complete_achieved() -> None:
    conv = ConversationManager(max_turns=10, max_noise_retries=3)
    assert conv.is_complete("Great, confirmed! [OBJECTIVE_ACHIEVED]") is True


def test_is_complete_failed() -> None:
    conv = ConversationManager(max_turns=10, max_noise_retries=3)
    assert conv.is_complete("Sorry, no availability. [OBJECTIVE_FAILED]") is True


def test_is_complete_not_done() -> None:
    conv = ConversationManager(max_turns=10, max_noise_retries=3)
    assert conv.is_complete("When would you prefer?") is False


def test_format_history() -> None:
    conv = ConversationManager(max_turns=10, max_noise_retries=3)
    conv.add_agent_message("Hello!", session_id=1)
    conv.add_interlocutor_message("Hi", intent=None, session_id=1)

    formatted = conv.format_history()
    assert "Agent: Hello!" in formatted
    assert "Interlocutor: Hi" in formatted


def test_has_objective_achieved_true() -> None:
    conv = ConversationManager(max_turns=10, max_noise_retries=3)
    conv.add_agent_message("Confirmed [OBJECTIVE_ACHIEVED]", session_id=1)
    assert conv.has_objective_achieved() is True


def test_has_objective_achieved_false() -> None:
    conv = ConversationManager(max_turns=10, max_noise_retries=3)
    conv.add_agent_message("Still talking", session_id=1)
    assert conv.has_objective_achieved() is False


def test_has_objective_achieved_failed_not_achieved() -> None:
    conv = ConversationManager(max_turns=10, max_noise_retries=3)
    conv.add_agent_message("Sorry [OBJECTIVE_FAILED]", session_id=1)
    assert conv.has_objective_achieved() is False


def test_log_line_has_timestamp() -> None:
    conv = ConversationManager(max_turns=10, max_noise_retries=3)
    conv.add_agent_message("Hello!", session_id=1)
    assert conv.log_lines[0].timestamp is not None
    assert isinstance(conv.log_lines[0].timestamp, datetime)


def test_noise_retries_initial_value() -> None:
    conv = ConversationManager(max_turns=10, max_noise_retries=3)
    assert conv.noise_retries == 0
    assert conv.max_noise_retries == 3
    assert conv.max_turns == 10
