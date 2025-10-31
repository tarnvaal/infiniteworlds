from fastapi import FastAPI

from .routers.chat import router as chat_router
from .dependencies import get_chatter


app = FastAPI(title="Infinite Worlds API")


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(chat_router)


@app.on_event("startup")
def _startup_warm_model():
    # Ensure the model is loaded at startup using MODEL_PATH env
    get_chatter()
