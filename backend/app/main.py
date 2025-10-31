from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers.chat import router as chat_router
from .dependencies import get_chatter


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure the model is loaded at startup using MODEL_PATH env
    get_chatter()
    yield
    # Shutdown: (if needed in the future)


app = FastAPI(title="Infinite Worlds API", lifespan=lifespan)

# allow React dev server to talk to API in development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(chat_router)
