# test_history.py
from backend.app.utility.history import History


def _make_history(
    max_history_tokens=100,
    system_prompt="You are a helpful assistant.",
    system_role="assistant",
    tokens=10,
):
    return History(max_history_tokens, system_prompt, system_role, tokens)


def test_history_creation():
    history = _make_history()
    assert history.max_history_tokens == 100
    assert len(history.history) == 1
    assert history.history[0].role == "assistant"
    assert history.history[0].content == "You are a helpful assistant."
    assert history.history[0].tokens == 10
    assert history.history[0].id == 0
    assert history.history[0].active


def test_add_message():
    history = _make_history()
    history.add_message("user", "Hello, how are you?", 10)
    assert len(history.history) == 2
    assert history.history[1].role == "user"
    assert history.history[1].content == "Hello, how are you?"
    assert history.history[1].tokens == 10
    assert history.history[1].id == 1
    assert history.history[1].active
    assert len(history.history) == 2


def test_select_messages():
    history = _make_history()
    history.add_message("user", "Hello, how are you?", 10)
    history.add_message("assistant", "I'm doing well, thank you!", 10)
    history.add_message("user", "What is your name?", 10)
    history.add_message("assistant", "My name is Assistant.", 10)
    selected = history._select_messages()
    assert len(selected) == 5
    assert selected[0].role == "assistant"
    assert selected[0].content == "You are a helpful assistant."
    assert selected[1].role == "user"
    assert selected[1].content == "Hello, how are you?"
    assert selected[2].role == "assistant"
    assert selected[2].content == "I'm doing well, thank you!"
    assert selected[3].role == "user"
    assert selected[3].content == "What is your name?"
    assert selected[4].role == "assistant"
    assert selected[4].content == "My name is Assistant."


def test_build_context():
    history = _make_history()
    history.add_message("user", "Hello, how are you?", 10)
    history.add_message("assistant", "I'm doing well, thank you!", 10)
    history.add_message("user", "What is your name?", 10)
    history.add_message("assistant", "My name is Assistant.", 100)
    context = history.build_context()
    assert len(context) == 4
    assert context[0]["role"] == "assistant"
    assert context[0]["content"] == "You are a helpful assistant."
    assert context[1]["role"] == "user"
    assert context[1]["content"] == "Hello, how are you?"


def test_deactivate_message():
    history = _make_history()
    history.add_message("user", "Hello, how are you?", 10)
    history.add_message("assistant", "I'm doing well, thank you!", 10)
    history.add_message("user", "What is your name?", 10)
    history.add_message("assistant", "My name is Assistant.", 100)
    context = history.build_context()
    assert len(context) == 4
    assert context[0]["role"] == "assistant"
    assert context[0]["content"] == "You are a helpful assistant."
    assert context[1]["role"] == "user"
    assert context[1]["content"] == "Hello, how are you?"


def test_recency_bias():
    history = _make_history()
    history.add_message("user", "Hello, how are you?", 10)
    history.add_message("assistant", "I'm doing well, thank you!", 10)
    history.add_message("user", "What is your name?", 10)
    history.add_message("assistant", "My name is Assistant.", 100)
    context = history.build_context()
    assert len(context) == 4
    assert context[0]["role"] == "assistant"
    assert context[0]["content"] == "You are a helpful assistant."
    assert context[1]["role"] == "user"
    assert context[1]["content"] == "Hello, how are you?"
    assert context[2]["role"] == "assistant"
    assert context[2]["content"] == "I'm doing well, thank you!"
    assert context[3]["role"] == "user"
    assert context[3]["content"] == "What is your name?"
    assert history.history[0].active
    assert history.history[1].active
    assert history.history[2].active
    assert history.history[3].active
    assert not history.history[4].active
