from contextlib import asynccontextmanager
import os
import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers.chat import router as chat_router
from .dependencies import get_chatter


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Preload the model in the background so health is immediate
    asyncio.create_task(asyncio.to_thread(get_chatter))
    yield
    # Shutdown: (if needed in the future)


app = FastAPI(title="PersistentDM API", lifespan=lifespan)

# allow React dev server to talk to API in development
# Support dynamic frontend port (Vite may use 5173-5180 range)
FRONTEND_PORT = os.getenv("FRONTEND_PORT", "5173")
allowed_origins = []
# Allow all common Vite ports (5173-5180) for both localhost and 127.0.0.1
for port in range(5173, 5181):  # 5181 to include 5180
    allowed_origins.extend(
        [
            f"http://localhost:{port}",
            f"http://127.0.0.1:{port}",
        ]
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(chat_router)
