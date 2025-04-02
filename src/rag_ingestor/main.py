from fastapi import FastAPI
from contextlib import asynccontextmanager

from rag_ingestor.config import settings, logger
from rag_ingestor.routes import router
from rag_ingestor.adapters.queue.factory import get_message_queue


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events for the application

    Args:
        app: FastAPI application
    """
    # On startup: Initialize services
    logger.info("Initializing services...")
    # Choose the message queue implementation you want to use
    message_queue = get_message_queue(queue_type="kafka")  # or "memory" for testing
    await message_queue.initialize()
    app.state.message_queue = message_queue  # Store for use in route handlers if needed
    logger.info("Services initialized")

    yield

    # On shutdown: Clean up resources
    logger.info("Shutting down services...")
    await message_queue.shutdown()
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
