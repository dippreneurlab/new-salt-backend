from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .core.database import close_pool, get_pool
from .routers import metadata, overhead, pipeline, quotes, roles, storage


@asynccontextmanager
async def lifespan(app: FastAPI):
    await get_pool()  # Warm pool on startup
    yield
    await close_pool()


app = FastAPI(
    title="QuoteHub Backend",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(storage.router, prefix=settings.api_prefix, tags=["storage"])
app.include_router(pipeline.router, prefix=settings.api_prefix, tags=["pipeline"])
app.include_router(quotes.router, prefix=settings.api_prefix, tags=["quotes"])
app.include_router(overhead.router, prefix=settings.api_prefix, tags=["overhead"])
app.include_router(roles.router, prefix=settings.api_prefix, tags=["roles"])
app.include_router(metadata.router, prefix=settings.api_prefix, tags=["metadata"])


@app.get("/health")
async def health():
    return {"status": "ok"}
