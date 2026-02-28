from fastapi import APIRouter

from app.config import settings

router = APIRouter(prefix="/api/v1/ai", tags=["AI"])


@router.get("/models", summary="List available AI models")
async def list_ai_models():
    """Expose selectable AI model options for the frontend."""
    free_models = [m.strip() for m in settings.AI_OPENROUTER_FREE_MODELS if m.strip()]
    default_model = settings.AI_OPENROUTER_MODEL.strip() or (free_models[0] if free_models else "")

    return {
        "enabled": settings.AI_INTEGRATIONS_ENABLED,
        "providers": [p.strip().lower() for p in settings.AI_PROVIDERS if p.strip()],
        "default_model": default_model,
        "models": free_models,
    }
