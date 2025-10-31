# test_message.py
from datetime import datetime
from backend.app.utility.message import Message


def _make_message(
    role="test",
    content="This is a test message",
    tokens=10,
    msg_id=1,
    active=True,
    timestamp=None,
):
    if timestamp is None:
        timestamp = datetime(2025, 1, 1, 12, 0, 0)

    return Message(
        role=role,
        content=content,
        tokens=tokens,
        msg_id=msg_id,
        active=active,
        timestamp=timestamp,
    )


def test_message_creation():
    ts = datetime(2025, 1, 1, 12, 0, 0)
    message = Message(
        role="test",
        content="This is a test message",
        tokens=10,
        msg_id=1,
        active=True,
        timestamp=ts,
    )

    assert message.role == "test"
    assert message.content == "This is a test message"
    assert message.tokens == 10
    assert message.id == 1
    assert message.is_active() is True
    assert message.timestamp == ts


def test_message_default_active_is_true():
    message = _make_message(active=True)
    assert message.is_active() is True


def test_message_deactivation():
    message = _make_message(active=True)
    message.deactivate()
    assert message.is_active() is False
    assert message.active is False


def test_message_activation():
    message = _make_message(active=False)
    message.activate()
    assert message.is_active() is True
    assert message.active is True


def test_message_str_format():
    message = _make_message(
        role="assistant",
        content="The dragon roars.",
        tokens=15,
        msg_id=99,
    )
    assert str(message) == "assistant: The dragon roars."
