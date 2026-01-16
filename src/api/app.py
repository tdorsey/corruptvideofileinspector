"""FastAPI application setup with GraphQL and OIDC authentication."""

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter

from src.api.graphql.schema import schema
from src.api.rest import router as rest_router
from src.api.security import get_oidc_config
from src.config import load_config

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> Any:
    """Lifespan context manager for FastAPI application."""
    # Startup
    logger.info("Starting corrupt-video-inspector API")
    config = load_config()
    logger.info(f"Loaded configuration from: {config}")
    yield
    # Shutdown
    logger.info("Shutting down corrupt-video-inspector API")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    config = load_config()

    app = FastAPI(
        title="Corrupt Video Inspector API",
        description="GraphQL API for video corruption detection and reporting",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add GraphQL endpoint with OIDC protection
    oidc_config = get_oidc_config()
    graphql_app = GraphQLRouter(
        schema,
        context_getter=lambda: {"config": config, "oidc": oidc_config},
    )
    app.include_router(graphql_app, prefix="/graphql")

    # Add REST API endpoints
    app.include_router(rest_router)

    # Health check endpoint
    @app.get("/health")
    async def health_check() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "healthy", "service": "corrupt-video-inspector-api"}

    # Metadata endpoint
    @app.get("/")
    async def root() -> dict[str, Any]:
        """Root endpoint with API information."""
        return {
            "name": "Corrupt Video Inspector API",
            "version": "1.0.0",
            "graphql_endpoint": "/graphql",
            "rest_endpoints": {
                "scans": "/api/scans",
                "websocket": "/ws/scans/{id}",
            },
            "health_endpoint": "/health",
        }

    return app
