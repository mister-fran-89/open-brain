from fastapi import FastAPI
from contextlib import asynccontextmanager

from src import __version__
from src.config import settings
from src.api.capture import router as capture_router
from src.api.query import router as query_router
from src.api.digest import router as digest_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure directories exist
    settings.vault_path.mkdir(parents=True, exist_ok=True)
    settings.data_path.mkdir(parents=True, exist_ok=True)
    (settings.vault_path / "_inbox").mkdir(exist_ok=True)
    (settings.vault_path / "_index").mkdir(exist_ok=True)
    for category in ["people", "projects", "ideas", "admin"]:
        (settings.vault_path / category).mkdir(exist_ok=True)
    yield
    # Shutdown: cleanup if needed


app = FastAPI(
    title="Open Brain",
    description="Personal knowledge capture and retrieval system",
    version=__version__,
    lifespan=lifespan,
)

# Include routers
app.include_router(capture_router)
app.include_router(query_router)
app.include_router(digest_router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": __version__}
