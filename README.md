# Infinite Worlds

A text-based interactive fiction system where an AI acts as a dungeon master.

## Files

- `main.py` - Entry point with interactive chat loop
- `utility/llama.py` - LLM wrapper and chat interface
- `utility/history.py` - Conversation history management with token limits
- `utility/message.py` - Message representation

## Installation

```bash
pip install -r requirements.txt
```

## Usage

1. Update the model path in `main.py`
2. Run: `python main.py`
3. Type "exit", "quit", or "bye" to end
