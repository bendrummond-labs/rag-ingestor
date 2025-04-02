from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
    BackgroundTasks,
    status,
    Query,
)
from pathlib import Path
import uuid
from typing import Dict, List, Optional

from rag_ingestor.ingestion.text_splitter import split_text, SplitterType
from rag_ingestor.ingestion.file_loader import _LOADER_REGISTRY
from rag_ingestor.schemas import IngestResponse
from rag_ingestor.config import settings, logger
from rag_ingestor.services.embedder import embedder_service

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
    """
    Returns list of supported text splitter types
    """
    return {"splitter_types": [t.value for t in SplitterType]}


@router.post(
    "/ingest", status_code=status.HTTP_202_ACCEPTED, response_model=IngestResponse
)
async def ingest_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    chunk_size: int = Query(500, gt=0, description="Maximum size of each chunk"),
    chunk_overlap: int = Query(
        100, ge=0, description="Overlap between consecutive chunks"
    ),
    splitter_type: SplitterType = Query(
        SplitterType.RECURSIVE, description="Text splitter algorithm to use"
    ),
    separate_by_headers: Optional[bool] = Query(
        False, description="Use header-based splitting for applicable documents"
    ),
    extract_metadata: bool = Query(True, description="Extract metadata from document"),
):
    # Validate chunk parameters
    if chunk_overlap >= chunk_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid chunk parameters. chunk_overlap must be less than chunk_size.",
        )

    file_id = str(uuid.uuid4())
    logger.info(f"Processing file: {file.filename} with ID: {file_id}")

    # Check file size
    file_size = 0
    contents = b""
    while chunk := await file.read(1024):
        file_size += len(chunk)
        contents += chunk
        if file_size > settings.MAX_FILE_SIZE:
            logger.warning(f"File too large: {file_size} bytes")
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE} bytes",
            )

    # Reset file pointer
    await file.seek(0)

    # Check file type
    ext = Path(file.filename).suffix.lower()
    if ext not in _LOADER_REGISTRY:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {ext}. Supported: {list(_LOADER_REGISTRY.keys())}",
        )

    # Auto-select appropriate splitter based on file type if not specified
    if splitter_type == SplitterType.RECURSIVE:
        if ext == ".md" and separate_by_headers:
            splitter_type = SplitterType.MARKDOWN
        elif ext == ".py":
            splitter_type = SplitterType.PYTHON
        elif ext == ".tex" or ext == ".latex":
            splitter_type = SplitterType.LATEX
        elif ext == ".html" or ext == ".htm":
            splitter_type = SplitterType.HTML

    # Process file content using the appropriate loader
    try:
        loader = _LOADER_REGISTRY[ext]
        text = loader.load(contents)  # Use the specific loader for the file type
        logger.info(f"File loaded and parsed, content length: {len(text)} characters")
    except Exception as e:
        logger.error(f"Failed to load file {file.filename}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process file: {str(e)}",
        )

    # Split text using the specified splitter
    kwargs = {}
    if separate_by_headers and splitter_type == SplitterType.HTML:
        # Add custom header configuration for HTML if needed
        kwargs = {
            "headers_to_split_on": [
                ("h1", 5),
                ("h2", 4),
                ("h3", 3),
                ("h4", 2),
            ]
        }

    chunks = split_text(
        text,
        splitter_type=splitter_type,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        **kwargs,
    )

    metadata = None
    if extract_metadata:
        # Generate metadata for each chunk (implementation depends on your needs)
        metadata = generate_chunk_metadata(file.filename, chunks)

    logger.info(f"File split into {len(chunks)} chunks using {splitter_type} splitter")

    # Process asynchronously
    background_tasks.add_task(
        process_document_async, file_id=file_id, chunks=chunks, metadata=metadata
    )

    return IngestResponse(
        status="processing",
        file_id=file_id,
        num_chunks=len(chunks),
        splitter_type=splitter_type,
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


def generate_chunk_metadata(filename: str, chunks: List[str]) -> List[Dict]:
    """Generate basic metadata for each chunk"""
    metadata = []
    for i, chunk in enumerate(chunks):
        metadata.append(
            {
                "chunk_index": i,
                "source_file": filename,
                "char_count": len(chunk),
                "word_count": len(chunk.split()),
            }
        )
    return metadata


async def process_document_async(
    file_id: str, chunks: List[str], metadata: Optional[List[Dict]] = None
):
    """Process document chunks asynchronously"""
    logger.info(
        f"Starting async processing for file ID: {file_id} with {len(chunks)} chunks"
    )

    # Send chunks to embedder service
    success = await embedder_service.embed_chunks(file_id, chunks, metadata)

    if success:
        logger.info(
            f"Document processing completed successfully for file ID: {file_id}"
        )
    else:
        logger.error(f"Document processing encountered issues for file ID: {file_id}")
