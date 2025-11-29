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

# Explicitly allow local + Cloud Run frontend origins without relying on env vars
DEFAULT_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://salthub-new-628837369388.us-central1.run.app",
]
# Allow any *.run.app host as a safety net for preview deployments
RUN_APP_ORIGIN_REGEX = r"https://.*run\.app"

# Merge configured origins with our safe defaults and de-dupe
configured_origins = settings.cors_origins or []
if "*" in configured_origins:
    allowed_origins = ["*"]
    origin_regex = RUN_APP_ORIGIN_REGEX
else:
    allowed_origins = list(dict.fromkeys(configured_origins + DEFAULT_CORS_ORIGINS))
    origin_regex = RUN_APP_ORIGIN_REGEX

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=origin_regex,
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
