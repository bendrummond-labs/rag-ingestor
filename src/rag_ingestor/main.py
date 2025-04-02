from fastapi import FastAPI
from rag_ingestor.routes import router

app = FastAPI(
    title="Document Ingestor Service",
    description="Service for ingesting, chunking and processing documents",
    version="1.0.0",
)

app.include_router(router)


@app.get("/")
async def root():
    return {"service": "RAG Document Ingestor", "version": "1.0.0", "docs_url": "/docs"}
