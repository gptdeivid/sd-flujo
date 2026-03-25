"""FastAPI main application."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes.health import router as health_router
from src.api.routes.tickets import router as tickets_router
from src.config.settings import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    settings = get_settings()
    logger.info(f"Starting Service Desk API in {settings.app_env} mode")
    logger.info(f"Using LLM model: {settings.llm_model}")

    yield

    # Shutdown
    logger.info("Shutting down Service Desk API")


# Create FastAPI app
app = FastAPI(
    title="Service Desk Multi-Agent API",
    description="Multi-agent Service Desk system using LangGraph and Gemini",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(tickets_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Service Desk Multi-Agent API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }
