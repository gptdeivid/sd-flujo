"""Health check endpoints."""

from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run."""
    return {
        "status": "healthy",
        "service": "servicedesk-agent",
    }


@router.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    # Could add dependency checks here (DB, LLM connectivity, etc.)
    return {
        "status": "ready",
        "checks": {
            "api": True,
            "graph": True,
        },
    }
