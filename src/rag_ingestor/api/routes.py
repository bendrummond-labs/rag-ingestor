import uuid
import os
import tempfile
from fastapi import APIRouter, File, HTTPException, UploadFile
from pathlib import Path

from rag_ingestor.application.services import DocumentService

router = APIRouter()


def get_document_service():
    from rag_ingestor.adapters.outbound.langchain.document_loader_adapter import (
        LangchainDocumentLoaderAdapter,
    )

    return DocumentService(document_loader=LangchainDocumentLoaderAdapter())


@router.get("/")
async def root():
    return {"message": "Welcome to the RAG Ingestor API!"}


@router.get("/health")
async def health_check():
    return {"status": "healthy"}


@router.post("/ingest", response_model=dict)
async def ingest_document(file: UploadFile = File(...)):
    """
    Ingest a document into the RAG system.
    """

    document_service = get_document_service()

    file_extension = os.path.splitext(file.filename)[1].lower()
    if not file_extension:
        raise HTTPException(
            status_code=400, detail="File does not have a valid extension."
        )

    supported_extensions = document_service.get_supported_extensions()

    if file_extension not in supported_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_extension}. Supported types are: {supported_extensions}",
        )

    with tempfile.NamedTemporaryFile(suffix=file_extension, delete=False) as temp_file:
        try:
            content = await file.read()
            temp_file.write(content)
            temp_file.flush()

            file_path = Path(temp_file.name)

            result = await document_service.process_document(file, file_path)
            result["document_id"] = str(uuid.uuid4())

            return result

        finally:
            os.unlink(temp_file.name)
