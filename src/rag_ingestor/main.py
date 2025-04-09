import os
import tempfile
from typing import List
import uuid
from fastapi import FastAPI, File, HTTPException, UploadFile

from rag_ingestor.adapters.outbound.langchain.document_loader_adapter import (
    LangchainDocumentLoaderAdapter,
)
from rag_ingestor.domain.model import Content

app = FastAPI(
    title="RAG Ingestor",
    description="Service for ingesting documents into a RAG system",
    version="0.1.0",
)

document_loader = LangchainDocumentLoaderAdapter()


@app.get("/")
async def root():
    return {"message": "Welcome to the RAG Ingestor API!"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/ingest", response_model=dict)
async def ingest_document(file: UploadFile = File(...)):
    """
    Ingest a document into the RAG system.
    """
    file_extension = os.path.splitext(file.filename)[1].lower()
    supported_extensions = list(document_loader.loaders.keys())

    if file_extension not in supported_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_extension}. Supported types are: {supported_extensions}",
        )

    with tempfile.NamedTemporaryFile(delete=False) as temp_file:

        try:
            content = await file.read()
            temp_file.write(content)
            temp_file.flush()

            contents: List[Content] = document_loader.load_content(temp_file.name)

            return {
                "status": "success",
                "document_id": str(uuid.uuid4()),
                "filename": file.filename,
                "content_count": len(contents),
                "total_characters": sum(len(content.text) for content in contents),
            }

        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error processing document: {str(e)}"
            )
        finally:
            # Clean up the temp file
            os.unlink(temp_file.name)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
