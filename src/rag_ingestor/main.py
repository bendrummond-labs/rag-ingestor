import logging
from fastapi import FastAPI
import uvicorn

from rag_ingestor.api.routes import router
from rag_ingestor.api.dependencies import get_settings


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(
    title="RAG Ingestor",
    description="Service for ingesting documents into a RAG system",
    version=settings.app_version,
    debug=settings.debug,
)

app.include_router(router, prefix="/api/v1", tags=["api"])

if __name__ == "__main__":
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Message queue type: {settings.message_queue_type}")
    logger.info(f"Debug mode: {settings.debug}")

    uvicorn.run(
        "rag_ingestor.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
