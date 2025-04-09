from typing import Optional
import uuid
import os
import tempfile
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pathlib import Path

from rag_ingestor.adapters.outbound.langchain.text_chunking_adapter import (
    LangchainTextChunkingAdapter,
)
from rag_ingestor.api.dependencies import get_document_service, get_message_queue
from rag_ingestor.ports.outbound.message_queue_port import MessageQueuePort

router = APIRouter()


@router.get("/")
async def root():
    return {"message": "Welcome to the RAG Ingestor API!"}


@router.get("/health")
async def health_check():
    return {"status": "healthy"}


@router.post("/ingest", response_model=dict)
async def ingest_document(
    file: UploadFile = File(...),
    chunking_enabled: bool = Query(True, description="Enable text chunking"),
    chunk_size: Optional[int] = Query(None, description="Size of text chunks"),
    chunk_overlap: Optional[int] = Query(None, description="Overlap between chunks"),
    splitter_type: Optional[str] = Query(
        None, description="Type of text splitter to use (recursive_character or token)"
    ),
    publish_chunks: bool = Query(True, description="Publish chunks to message queue"),
    message_queue: MessageQueuePort = Depends(get_message_queue),
):
    """
    Ingest a document into the RAG system.
    """

    document_service = get_document_service(message_queue=message_queue)

    file_extension = os.path.splitext(file.filename)[1].lower()
    if not file_extension:
        raise HTTPException(
            status_code=400, detail="File does not have a valid extension."
        )

    chunk_params = None
    if chunking_enabled and any(
        param is not None for param in [chunk_size, chunk_overlap, splitter_type]
    ):
        chunk_params = {}
        if chunk_size is not None:
            chunk_params["chunk_size"] = chunk_size
        if chunk_overlap is not None:
            chunk_params["chunk_overlap"] = chunk_overlap
        if splitter_type is not None:
            if splitter_type not in ["recursive_character", "token"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported splitter type: {splitter_type}. "
                    f"Supported types are: recursive_character, token",
                )

    with tempfile.NamedTemporaryFile(suffix=file_extension, delete=False) as temp_file:
        try:
            # Read and write the uploaded file
            content = await file.read()
            temp_file.write(content)
            temp_file.flush()

            file_path = Path(temp_file.name)

            # Process the document
            if not chunking_enabled:
                # If chunking is disabled, use None for text_chunker
                document_service.text_chunker = None

            # Replace the chunker if a different splitter type is requested
            elif splitter_type is not None and document_service.text_chunker:
                document_service.text_chunker = LangchainTextChunkingAdapter(
                    splitter_type=splitter_type,
                    chunk_size=chunk_size or 1000,
                    chunk_overlap=chunk_overlap or 200,
                )

            # Process the document
            result = await document_service.process_document(
                file, file_path, chunk_params, publish_chunks
            )

            # Add document ID
            result["document_id"] = str(uuid.uuid4())

            return result

        finally:
            # Clean up the temporary file
            os.unlink(temp_file.name)


@router.get("/supported-extensions")
async def get_supported_extensions():
    """
    Get the list of supported file extensions.

    Returns:
        List of supported file extensions
    """
    document_service = get_document_service()
    return {"supported_extensions": document_service.get_supported_extensions()}


@router.get("/chunking-options")
async def get_chunking_options():
    """
    Get available text chunking options.

    Returns:
        Information about available chunking options
    """
    return {
        "splitter_types": ["recursive_character", "token"],
        "default_chunk_size": 1000,
        "default_chunk_overlap": 200,
        "recommendations": {
            "text_documents": {
                "splitter_type": "recursive_character",
                "chunk_size": 1000,
                "chunk_overlap": 200,
            },
            "code_or_structured_data": {
                "splitter_type": "token",
                "chunk_size": 500,
                "chunk_overlap": 50,
            },
        },
    }


@router.get("/queue-status")
async def get_queue_status(
    message_queue: MessageQueuePort = Depends(get_message_queue),
):
    """
    Get status information about the message queue.

    This endpoint is primarily useful for diagnostics and monitoring.
    For in-memory queues, it returns message counts; for Kafka, it returns
    connection status.

    Returns:
        Status information about the message queue
    """
    # Different behavior based on queue implementation
    if hasattr(message_queue, "get_chunks"):
        # This is an InMemoryMessageQueueAdapter
        return {
            "queue_type": "in-memory",
            "chunks_count": len(message_queue.get_chunks()),
            "events_count": len(message_queue.get_events()),
            "status": (
                "active" if not getattr(message_queue, "is_closed", False) else "closed"
            ),
        }
    else:
        # Assume it's a KafkaMessageQueueAdapter or similar
        return {
            "queue_type": "kafka",
            "bootstrap_servers": getattr(message_queue, "bootstrap_servers", "unknown"),
            "chunks_topic": getattr(message_queue, "chunks_topic", "document-chunks"),
            "events_topic": getattr(message_queue, "events_topic", "system-events"),
            "status": (
                "connected"
                if getattr(message_queue, "producer", None) is not None
                else "disconnected"
            ),
        }
