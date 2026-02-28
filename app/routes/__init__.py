from fastapi import APIRouter
from .health import router as health_router
from .upload import router as upload_router
from .github import router as github_router
from .report import router as report_router
from .stream import router as stream_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(upload_router, prefix="/api/v1")
api_router.include_router(github_router, prefix="/api/v1")
api_router.include_router(report_router, prefix="/api/v1")
api_router.include_router(stream_router, prefix="/api/v1")
