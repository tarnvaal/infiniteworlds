# Infinite Worlds

A text-based interactive fiction system where an AI acts as a dungeon master.

## Files

- `backend/app/main.py` - FastAPI application (health + chat endpoints)
- `backend/app/utility/llama.py` - LLM wrapper and chat interface
- `backend/app/utility/history.py` - Conversation history management with token limits
- `backend/app/utility/message.py` - Message representation

## Installation

```bash
pip install -r requirements.txt
```

## Usage

1. Set model path (optional; defaults to `~/dev/llm/Harbinger-24B-Q5_K_M.gguf`):
   - Linux/macOS: `export MODEL_PATH=/absolute/path/to/model.gguf`
   - Windows (PowerShell): `$Env:MODEL_PATH = "C:\\path\\to\\model.gguf"`
2. Install server deps (suggested):
   ```bash
   pip install fastapi "uvicorn[standard]"
   ```
3. Run API server:
   ```bash
   uvicorn backend.app.main:app --reload
   ```
4. Test endpoints:
   - Health: `GET /health`
   - Chat: `POST /chat` with JSON `{ "message": "Hello" }`

The frontend will be a NodeJS app and can call these endpoints.
