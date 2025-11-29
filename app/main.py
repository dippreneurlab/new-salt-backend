from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .core.config import settings
from .core.database import close_pool, get_pool
from .routers import metadata, overhead, pipeline, quotes, roles, storage


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     await get_pool()  # Warm pool on startup
#     yield
#     await close_pool()


app = FastAPI(
    title="QuoteHub Backend",
    version="1.0.0",
    # lifespan=lifespan,
)

# Explicitly allow local + Cloud Run frontend origins without relying on env vars
# Explicitly allow local + Cloud Run frontend origins without relying on env vars
DEFAULT_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://salthub-new-628837369388.us-central1.run.app",  # Frontend URL (ADD THIS)
    "https://salthub-new-backend-628837369388.us-central1.run.app",  # Backend URL
]
# Allow any *.run.app host as a safety net for preview deployments
RUN_APP_ORIGIN_REGEX = r"https://.*run\.app"

# Merge configured origins with our safe defaults (drop '*' because we set credentials=True)
configured_origins = [o for o in settings.cors_origins or [] if o and o != "*"]
allowed_origins = list(dict.fromkeys(DEFAULT_CORS_ORIGINS + configured_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=RUN_APP_ORIGIN_REGEX,
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


STAFF_CSV_PATH = Path(__file__).resolve().parent.parent / "Salt_staff.csv"


@app.get("/Salt_staff.csv")
async def get_staff_csv():
    if STAFF_CSV_PATH.exists():
        return FileResponse(STAFF_CSV_PATH, media_type="text/csv")
    raise HTTPException(status_code=404, detail="Staff CSV not found")
