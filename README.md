# PersistentDM

A text-based interactive fiction system where an AI acts as a dungeon master.

## Installation
```bash
pip install -r requirements.txt
```

## Usage

Model GGUF files: [Harbinger-24B-GGUF](https://huggingface.co/LatitudeGames/Harbinger-24B-GGUF)

1. Optional: set `MODEL_PATH` (defaults to `~/dev/llm/Harbinger-24B-Q5_K_M.gguf`). Requires an NVIDIA GPU with ~23 GiB free VRAM.
   - Linux/macOS: `export MODEL_PATH=/absolute/path/to/model.gguf`
   - Windows (PowerShell): `$Env:MODEL_PATH = "C:\\path\\to\\model.gguf"`
2. Run API server:
   ```bash
   uvicorn backend.app.main:app --reload
   ```
3. Test endpoints:
   - Health: `GET /health`
   - Chat: `POST /chat` with JSON `{ "message": "Hello" }`
   - See `requests.rest` for ready-made requests

## Node.js

- Target: Node 18+ (built-in `fetch`).
- Set `API_BASE_URL` as needed (e.g., `http://localhost:8000`).

## Important Installation Notes

MUST be built from source with CUDA enabled, do NOT let pip pull CPU wheel

To install on a fresh venv:

```bash
CMAKE_ARGS="-DGGML_CUDA=on" \
pip install --no-binary=:all: --no-cache-dir llama-cpp-python==0.3.16
```
