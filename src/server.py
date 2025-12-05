"""FastAPI application setup and configuration."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import webhook_router
from src.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager.

    Args:
        app: FastAPI application instance
    """
    # Startup
    logger.info("Starting application...")
    settings.ensure_audio_cache_dir()
    logger.info(f"Audio cache directory: {settings.audio_cache_dir}")

    yield

    # Shutdown
    logger.info("Shutting down application...")
    # Clean up notification service resources
    from src.api.webhooks import notification

    await notification.cleanup()
    logger.info("Cleanup complete")


def create_app() -> FastAPI:
    """Create and configure FastAPI application.

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="Xiaomi Speaker Notification Service",
        description="GitHub notification system for Xiaomi speaker using MiService and Edge TTS",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins for webhooks
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(webhook_router)

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy"}

    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint with service information."""
        return {
            "service": "Xiaomi Speaker Notification Service",
            "version": "0.1.0",
            "endpoints": {
                "health": "/health",
                "github_webhook": "/webhook/github",
                "custom_notification": "/webhook/custom",
            },
        }

    return app


# Create application instance
app = create_app()
