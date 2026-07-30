"""API route registration.

All API routers are aggregated here and mounted under /api/v1 by the
application factory in main.py.
"""

from fastapi import APIRouter

from app.api.analysis import router as analysis_router
from app.api.auth import router as auth_router
from app.api.downloads import router as downloads_router
from app.api.jobs import router as jobs_router
from app.api.resumes import router as resumes_router

router = APIRouter()

# ─── Include sub-routers ─────────────────────────────────────────────────────
router.include_router(auth_router)
router.include_router(resumes_router)
router.include_router(jobs_router)
router.include_router(analysis_router)
router.include_router(downloads_router)


@router.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Basic health check endpoint.

    Returns service status and version for load balancer probes
    and monitoring systems.
    """
    return {
        "status": "healthy",
        "version": "0.1.0",
    }
