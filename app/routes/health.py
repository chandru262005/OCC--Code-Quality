from fastapi import APIRouter
from fastapi.responses import RedirectResponse

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Health check endpoint")
async def health_check():
    """Returns the health status and version of the API."""
    return {"status": "healthy", "version": "1.0.0"}


@router.get("/", summary="Root redirect", include_in_schema=False)
async def root():
    """Redirect root to API docs."""
    return RedirectResponse(url="/docs")
