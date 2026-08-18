"""FastAPI application entrypoint.

Wires together configuration, logging, CORS, exception handlers, and the
domain routers. Run locally with:

    uvicorn app.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import applications as applications_routes
from app.api import auth as auth_routes
from app.api import companies as companies_routes
from app.api import drives as drives_routes
from app.api import student as student_routes
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging

configure_logging()
settings = get_settings()

app = FastAPI(
    title="Placement Portal API",
    description="Backend API for the college placement portal.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(auth_routes.router)
app.include_router(student_routes.router)
app.include_router(companies_routes.router)
app.include_router(drives_routes.router)
app.include_router(applications_routes.router)


@app.get("/health", tags=["Health"], summary="Health check")
async def health_check() -> dict:
    """Lightweight liveness check. Does not touch the database."""
    return {"status": "ok"}