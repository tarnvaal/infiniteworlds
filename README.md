# PersistentDM

A text-based interactive fiction system that uses large language models to generate persistent world states and narrative responses.

## Overview

PersistentDM implements an AI dungeon master for text-based role-playing games. The system maintains persistent world state through a vector-based memory system and provides conversational interfaces for game interactions.

### Key Features

- Persistent world memory with vector similarity search
- World-aware replies: injects relevant World Facts and NPC Cards into the LLM prompt
- Automatic memory extraction from each conversation turn (stores significant facts/NPC snapshots)
- FastAPI backend with automatic CORS handling
- React frontend with Tailwind CSS
- Llama.cpp integration for local LLM inference
- Automated development environment setup

## Architecture

### Backend

- **Framework**: FastAPI with automatic API documentation
- **LLM Integration**: llama-cpp-python with CUDA acceleration
- **World Memory**: Vector-based memory system using embeddings for similarity search
- **Conversation Orchestration**: `ConversationService` composes `Chatter` and `WorldMemory`, retrieves relevant memories and NPC snapshots, formats World Facts + NPC Cards, injects them into the LLM call, and persists new memories
- **Model**: Harbinger-24B-GGUF (quantized for ~23GB VRAM usage)

### Frontend

- **Framework**: React 18 with Vite build system
- **Styling**: Tailwind CSS 4.x
- **Development**: Hot reload with concurrent backend proxying

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- **NVIDIA GPU with 24GB+ VRAM (required for model inference)**
- **CUDA toolkit (required for GPU acceleration)**

### Quick Setup

Run the automated setup script:

```bash
./scripts/setup.sh
```

This creates a Python virtual environment, installs dependencies, and sets up the frontend.

### Manual Setup

1. Create Python virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Install frontend dependencies:
   ```bash
   cd frontend && npm install
   ```

### Model Configuration

Download the required model file: [Harbinger-24B-GGUF](https://huggingface.co/LatitudeGames/Harbinger-24B-GGUF)

Set the model path:
```bash
export MODEL_PATH=/absolute/path/to/Harbinger-24B-Q5_K_M.gguf
```
Optionally set the maximum model context window (default 16384 tokens):
```bash
export MAX_CONTEXT_TOKENS=16384
```


Default path: `~/dev/llm/Harbinger-24B-Q5_K_M.gguf`

### CUDA Installation

**CRITICAL**: The llama-cpp-python package must be built from source with CUDA support enabled. Do NOT install the CPU-only wheel from PyPI.

```bash
CMAKE_ARGS="-DGGML_CUDA=on" \
pip install --no-binary=:all: --no-cache-dir llama-cpp-python==0.3.16
```

GPU acceleration is required for practical inference speeds with the 24B parameter model.

## Running the Application

### Development Mode

Start both backend and frontend simultaneously:

```bash
npm run dev
```

This runs:
- Backend API on `http://localhost:8000`
- Frontend dev server on `http://localhost:5173`

### Individual Services

Start backend only:
```bash
npm run api
# or
uvicorn backend.app.main:app --reload
```

Start frontend only:
```bash
npm run web
# or
cd frontend && npm run dev
```

### Production Build

```bash
cd frontend && npm run build
cd frontend && npm run preview
```

## API Endpoints

- `GET /health` - Health check
- `POST /chat` - Send chat message
- `POST /chat/clear` - Clear conversation history

See `requests.rest` for example API calls.

### Request Flow (Chat)
- Frontend POSTs `{ "message": string }` to `/chat`
- Backend router delegates to `ConversationService.handle_user_message`
- Service retrieves relevant memories (weighted by similarity/recency/type) and NPC snapshots
- Service formats World Facts and NPC Cards and injects them as a transient system message
- `Chatter.chat` generates the DM reply; the service analyzes the turn and stores new durable memories when confidence is high
- Response returns `{ "reply": string }` (no world/memory details are exposed to the client)

## Testing

Run the test suite:

```bash
npm test
# or
pytest
```

Tests are located in `backend/tests/` and cover:
- API endpoints
- Message handling
- History management

## Project Structure

```
PersistentDM/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── dependencies.py      # Dependency injection
│   │   ├── routers/
│   │   │   └── chat.py          # Chat API endpoints
│   │   ├── utility/
│   │   │   ├── embeddings.py    # Vector embeddings
│   │   │   └── llama.py         # LLM integration
│   │   └── world/
│   │       ├── memory.py              # World state memory (memories + NPC snapshots)
│   │       ├── context_builder.py     # Weighted retrieval and formatting (World Facts, NPC Cards)
│   │       ├── conversation_service.py# Orchestrates context injection + memory extraction
│   │       ├── memory_utils.py        # Helpers for sanitizing entities
│   │       ├── queries.py             # Memory/planner prompts
│   │       └── summarizer.py          # Memory summarization
│   └── tests/                   # Test suite
├── frontend/
│   ├── src/                     # React application
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
├── scripts/
│   ├── setup.sh                 # Development setup
│   └── run.sh                   # Development runner
├── requirements.txt             # Python dependencies
├── pyproject.toml               # Python project config
└── package.json                 # Root package scripts
```

## Code Quality

### Python

- **Formatting**: Black (88 character line length)
- **Linting**: Ruff
- **Type checking**: Pyright

Format code:
```bash
black .
ruff check . --fix
```

### JavaScript/TypeScript

- **Formatting**: Prettier (via Vite)
- **Linting**: ESLint (via Vite)

### Development Workflow

- Use the setup script for initial environment configuration
- Run tests before committing
- Follow existing code style and patterns
- Update documentation for API changes

## Dependencies

### Python

Key dependencies in `requirements.txt`:
- fastapi: Web framework
- llama-cpp-python: LLM inference
- numpy: Numerical operations
- sentence-transformers: Text embeddings

### Node.js

Key dependencies in `frontend/package.json`:
- react: UI framework
- vite: Build tool
- tailwindcss: CSS framework

## Environment Variables

- `MODEL_PATH`: Path to GGUF model file
- `FRONTEND_PORT`: Frontend development port (default: 5173)
- `API_BASE_URL`: Backend API URL for frontend

## Troubleshooting

### CUDA Issues

Ensure CUDA is properly installed and the llama-cpp-python package is built with CUDA support. Check GPU memory usage with `nvidia-smi`.

### Port Conflicts

The development scripts automatically handle common Vite port ranges (5173-5180). Adjust `FRONTEND_PORT` if needed.

### Model Loading

Model loading can take several minutes on first startup. The health endpoint will not respond until the model is fully loaded.
