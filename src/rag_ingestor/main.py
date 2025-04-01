from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, status
from fastapi.responses import JSONResponse
from .ingestion.chunker import chunk_text
from .ingestion.file_loader import load_text_file, detect_file_type, supported_file_types
import uuid
import httpx
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

EMBEDDER_URL = os.getenv("EMBEDDER_URL", "http://embedder:8002/embed")
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 10 * 1024 * 1024))  # 10MB default

app = FastAPI(title="Document Ingestor Service", 
             description="Service for ingesting, chunking and processing documents")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/supported-files")
async def get_supported_files():
    return {"supported_file_types": supported_file_types()}

@app.post("/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    chunk_size: int = 500, 
    chunk_overlap: int = 100
):
    file_id = str(uuid.uuid4())
    logger.info(f"Processing file: {file.filename} with ID: {file_id}")
    
    # Check file size
    file_size = 0
    contents = b""
    while chunk := await file.read(1024):
        file_size += len(chunk)
        contents += chunk
        if file_size > MAX_FILE_SIZE:
            logger.warning(f"File too large: {file_size} bytes")
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE} bytes"
            )
    
    # Reset file pointer
    await file.seek(0)
    
    # Check file type
    try:
        file_type = detect_file_type(file.filename)
        logger.info(f"Detected file type: {file_type}")
    except ValueError as e:
        logger.error(f"Unsupported file type: {file.filename}")
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=str(e)
        )
    
    # Process file content
    try:
        text = contents.decode("utf-8")
        logger.info(f"File decoded, length: {len(text)} characters")
    except UnicodeDecodeError:
        logger.error(f"Failed to decode file: {file.filename}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File encoding is not UTF-8"
        )
    
    # Chunk text
    chunks = chunk_text(text, chunk_size, chunk_overlap)
    logger.info(f"File chunked into {len(chunks)} chunks")
    
    # Process asynchronously
    background_tasks.add_task(send_to_embedder, file_id, chunks)
    
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={
            "file_id": file_id,
            "filename": file.filename,
            "num_chunks": len(chunks),
            "status": "processing"
        }
    )

async def send_to_embedder(file_id: str, chunks: list):
    logger.info(f"Sending {len(chunks)} chunks to embedder for file ID: {file_id}")
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                EMBEDDER_URL, 
                json={
                    "file_id": file_id,
                    "chunks": chunks
                }
            )
            response.raise_for_status()
            logger.info(f"Successfully sent chunks to embedder for file ID: {file_id}")
    except httpx.TimeoutException:
        logger.error(f"Timeout when calling embedder for file ID: {file_id}")
    except httpx.HTTPStatusError as e:
        logger.error(f"Embedder returned error {e.response.status_code} for file ID: {file_id}")
    except Exception as e:
        logger.error(f"Failed to call embedder for file ID: {file_id}: {str(e)}")