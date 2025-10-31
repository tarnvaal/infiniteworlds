from contextlib import asynccontextmanager

from fastapi import FastAPI

from .routers.chat import router as chat_router
from .dependencies import get_chatter


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure the model is loaded at startup using MODEL_PATH env
    get_chatter()
    yield
    # Shutdown: (if needed in the future)


app = FastAPI(title="Infinite Worlds API", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(chat_router)
