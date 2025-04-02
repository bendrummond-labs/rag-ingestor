import datetime
from typing import Dict, List
import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException, status
import tempfile
import os

from rag_ingestor.config import settings, logger
from rag_ingestor.adapters.loaders.base import _LOADER_REGISTRY
from rag_ingestor.adapters.splitters.factory import get_splitter_service
from rag_ingestor.schemas import IngestResponse
from rag_ingestor.services.kafka_producer import KafkaProducerService


def validate_chunking(chunk_size: int, chunk_overlap: int):
    if chunk_overlap >= chunk_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="chunk_overlap must be less than chunk_size",
        )


def validate_file_type(ext: str):
    if ext not in _LOADER_REGISTRY:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {ext}. Supported: {list(_LOADER_REGISTRY.keys())}",
        )


def read_file_contents(file: UploadFile) -> bytes:
    contents = b""
    size = 0
    while True:
        chunk = file.file.read(1024)
        if not chunk:
            break
        size += len(chunk)
        contents += chunk
        if size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Max allowed is {settings.MAX_FILE_SIZE} bytes.",
            )
    file.file.seek(0)
    return contents


def load_documents_from_bytes(contents: bytes, file_extension: str):
    """
    Helper function to create a temporary file and load documents.

    Args:
        contents: The file contents as bytes
        file_extension: The file extension including the dot (e.g., '.txt')

    Returns:
        List of documents loaded from the file

    Raises:
        Exception: If document loading fails
    """
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=file_extension
        ) as temp_file:
            temp_file.write(contents)
            temp_path = temp_file.name

        loader = _LOADER_REGISTRY[file_extension]
        return loader(temp_path)
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                logger.warning(f"Failed to remove temporary file {temp_path}: {e}")


async def _send_chunks_to_kafka(file_id: str, chunks: List[Dict]):
    try:
        producer = await KafkaProducerService.get_instance(
            topic=settings.KAFKA_TOPIC_EMBEDDINGS
        )
        await producer.send(
            {
                "file_id": file_id,
                "timestamp": datetime.datetime.now().isoformat(),
                "documents": chunks,
            }
        )
        logger.info(
            f"Sent {len(chunks)} chunks to Kafka topic '{settings.KAFKA_TOPIC_EMBEDDINGS}'"
        )
    except Exception as e:
        logger.error(f"Failed to send chunks to Kafka: {str(e)}")


async def ingest(
    file: UploadFile, splitter_type: str, chunk_size: int, chunk_overlap: int
) -> IngestResponse:
    """
    Process a document file, split it into chunks, and queue for embedding.

    Args:
        file: The uploaded document file
        splitter_type: Type of text splitter to use
        chunk_size: Size of each chunk in tokens/chars
        chunk_overlap: Overlap between chunks

    Returns:
        Response with processing status and metadata
    """
    file_id = str(uuid.uuid4())
    ext = Path(file.filename).suffix.lower()

    try:
        # Validate inputs
        validate_file_type(ext)
        validate_chunking(chunk_size, chunk_overlap)

        # Read file contents
        contents = read_file_contents(file)
        logger.info(f"File read: {file.filename}, size={len(contents)} bytes")

        # Load documents from file
        documents = load_documents_from_bytes(contents, ext)

        # Split documents
        splitter = get_splitter_service(splitter_type, chunk_size, chunk_overlap)
        chunks = splitter.split_documents(documents)

        logger.info(
            f"File processed: original docs={len(documents)}, chunks={len(chunks)}"
        )

        await _send_chunks_to_kafka(file_id, chunks)
        logger.info(
            f"File {file.filename} ingested successfully. "
            f"Chunks sent to Kafka topic '{settings.KAFKA_TOPIC_EMBEDDINGS}'"
        )

        return IngestResponse(
            status="processing",
            file_id=file_id,
            num_chunks=len(chunks),
        )

    except HTTPException:
        # Re-raise HTTP exceptions directly
        raise
    except Exception as e:
        logger.exception(f"Error processing file: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process file: {str(e)}",
        )
