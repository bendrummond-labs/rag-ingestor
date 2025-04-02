from fastapi import FastAPI
from contextlib import asynccontextmanager

from rag_ingestor.config import settings, logger
from rag_ingestor.routes import router
from rag_ingestor.di_container import initialize_container, shutdown_container


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events for the application

    Args:
        app: FastAPI application
    """
    # On startup: Initialize services using the DI container
    logger.info("Initializing services...")
    await initialize_container()
    logger.info("Services initialized")

    yield

    # On shutdown: Clean up resources using the DI container
    logger.info("Shutting down services...")
    await shutdown_container()
    logger.info("Services shutdown complete")


app = FastAPI(
    title="Document Ingestor Service",
    description="Service for ingesting, chunking and processing documents",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint providing basic service information"""
    return {
        "service": "RAG Document Ingestor",
        "version": "1.0.0",
        "docs_url": "/docs",
        "config": {
            "max_file_size_mb": settings.MAX_FILE_SIZE / (1024 * 1024),
        },
    }
