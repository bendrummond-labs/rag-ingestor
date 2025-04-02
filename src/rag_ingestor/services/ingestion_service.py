import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException, status

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


async def ingest(
    file: UploadFile, splitter_type: str, chunk_size: int, chunk_overlap: int
) -> IngestResponse:
    file_id = str(uuid.uuid4())
    ext = Path(file.filename).suffix.lower()

    validate_file_type(ext)
    validate_chunking(chunk_size, chunk_overlap)

    contents = read_file_contents(file)
    logger.info(f"File read: {file.filename}, size={len(contents)} bytes")

    try:
        loader = _LOADER_REGISTRY[ext]
        text = loader.load(contents)
    except Exception as e:
        logger.error(f"Error loading file: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to load file: {str(e)}",
        )

    splitter = get_splitter_service(splitter_type, chunk_size, chunk_overlap)
    documents = splitter.create_documents([text])
    logger.info(
        f"Split into {len(documents)} documents using '{splitter_type}' splitter"
    )

    # Send to Kafka for async processing
    producer = KafkaProducerService(topic="embedding-jobs")
    await producer.start()
    await producer.send(
        {
            "file_id": file_id,
            "documents": [doc.dict() for doc in documents],
        }
    )
    await producer.stop()

    return IngestResponse(
        status="processing",
        file_id=file_id,
        num_chunks=len(documents),
        splitter_type=splitter_type,
        documents=documents,
    )
