"""Health check route for the backend application."""

from fastapi import APIRouter


router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    """Return a simple status response for uptime checks."""
    return {"status": "ok"}

