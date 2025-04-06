from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Query,
)

from rag_ingestor.api.schemas import IngestResponse
from rag_ingestor.di_container import (
    get_ingestion_service,
    get_loader_manager,
    get_splitter_manager,
)

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
    loader_manager = get_loader_manager()
    return {"supported_file_types": list(loader_manager.loaders.keys())}


@router.get("/splitter-types")
async def get_splitter_types():
    splitter_manager = get_splitter_manager()
    return {"available_splitters": list(splitter_manager.splitter_types.keys())}


@router.post("/ingest")
async def ingest_document(
    file: UploadFile = File(...),
    chunk_size: int = Query(500),
    chunk_overlap: int = Query(100),
    splitter_type: str = Query("plain"),
):
    ingestions_service = get_ingestion_service()
    response = await ingestions_service.ingest(
        file, splitter_type, chunk_size, chunk_overlap
    )

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
