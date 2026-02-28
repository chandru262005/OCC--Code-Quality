from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pathlib import Path
import logging

from app.routes import api_router  # noqa: E402
from app.config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Startup and shutdown events."""
    # Startup: create temp directories
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.REPO_DIR).mkdir(parents=True, exist_ok=True)
    logger.info("Code Quality Gate API started")
    yield
    # Shutdown
    logger.info("Code Quality Gate API shutting down")


app = FastAPI(
    title=settings.APP_NAME,
    description="API for analyzing code quality through lint, static analysis, and security scanning",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routes
app.include_router(api_router)
