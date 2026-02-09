"""FastAPI application entry point."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import dashboard, decks, health, oss, settings as settings_router, study

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="LanGear API",
    description="LanGear MVP Backend - English Speaking Training Platform",
    version="2.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router)
app.include_router(oss.router)
app.include_router(decks.router)
app.include_router(study.router)
app.include_router(dashboard.router)
app.include_router(settings_router.router)

logger.info("LanGear API started successfully")


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("Starting LanGear API v2.0")
    logger.info(f"CORS origins: {settings.cors_origins_list}")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("Shutting down LanGear API")
