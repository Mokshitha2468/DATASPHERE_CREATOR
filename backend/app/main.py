"""Datasphere Creator - Backend Application Entrypoint."""

from __future__ import annotations
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes_sources import router as sources_router
from app.api.routes_plan import router as plan_router
from app.api.routes_state import router as state_router
from app.api.routes_logs import router as logs_router
from app.core.config import settings
from app.observability.logger import logger
from app.observability.tracing import init_tracing


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info("Initializing Datasphere Creator Backend...")
    init_tracing()
    yield
    logger.info("Shutting down Datasphere Creator Backend.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
    description="SAP Datasphere Modeling Planner and Source Engine."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers with /api prefix
app.include_router(sources_router, prefix=settings.API_PREFIX)
app.include_router(plan_router, prefix=settings.API_PREFIX)
app.include_router(state_router, prefix=settings.API_PREFIX)
app.include_router(logs_router, prefix=settings.API_PREFIX)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": settings.VERSION}
