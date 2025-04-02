from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Query,
)

from rag_ingestor.adapters.splitters.base import SPLITTER_SERVICE_REGISTRY
from rag_ingestor.adapters.loaders.base import _LOADER_REGISTRY
from rag_ingestor.schemas import IngestResponse
from rag_ingestor.services.ingestion_service import ingest

router = APIRouter(prefix="/api/v1", tags=["ingestor"])


@router.get("/health")
async def health_check():
    """
    Simple health check endpoint to verify service is running
    """
    return {"status": "healthy", "service": "rag-ingestor"}


@router.get("/supported-files")
async def get_supported_files():
    """
    Returns list of supported file extensions for ingestion
    """
    return {"supported_file_types": list(_LOADER_REGISTRY.keys())}


@router.get("/splitter-types")
async def get_splitter_types():
    return {"available_splitters": list(SPLITTER_SERVICE_REGISTRY.keys())}


@router.post("/ingest")
async def ingest_document(
    file: UploadFile = File(...),
    chunk_size: int = Query(500),
    chunk_overlap: int = Query(100),
    splitter_type: str = Query("plain"),
):
    response = await ingest(file, splitter_type, chunk_size, chunk_overlap)

    return IngestResponse(
        status="processing",
        file_id=response.file_id,
        num_chunks=response.num_chunks,
    )


@router.get("/job/{file_id}")
async def get_job_status(file_id: str):
    """
    Check the status of a document processing job

    Args:
        file_id: The unique identifier for the document processing job

    Returns:
        Status information for the job
    """
    # This would typically check a database or cache for job status
    # For now, just return a placeholder response
    return {
        "file_id": file_id,
        "status": "unknown",
        "message": "Job status tracking not yet implemented",
    }
