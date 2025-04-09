import logging
from fastapi import FastAPI

from rag_ingestor.api.routes import router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="RAG Ingestor",
    description="Service for ingesting documents into a RAG system",
    version="0.1.0",
)

app.include_router(router, prefix="/api", tags=["api"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
