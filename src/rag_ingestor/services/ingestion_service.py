from typing import Dict, List
import uuid
import logging
from fastapi import UploadFile, HTTPException, status

from rag_ingestor.config import settings
from rag_ingestor.api.schemas import IngestResponse
from rag_ingestor.services.document_service import DocumentService
from rag_ingestor.adapters.queue.base import MessageQueue


class IngestionService:
    def __init__(
        self,
        document_service: DocumentService,
        message_queue: MessageQueue,
    ):
        """
        Initialize the ingestion service

        Args:
            document_service: Service for document processing
            message_queue: Queue for sending messages
        """
        self.document_service = document_service
        self.message_queue = message_queue
        self.logger = logging.getLogger(__name__)

    async def send_chunks_to_queue(self, file_id: str, chunks: List[Dict]) -> bool:
        try:
            message = {
                "file_id": file_id,
                "documents": chunks,
            }

            success = await self.message_queue.send_message(
                settings.KAFKA_TOPIC_EMBEDDINGS, message
            )

            if success:
                self.logger.info(
                    f"Sent {len(chunks)} chunks to queue '{settings.KAFKA_TOPIC_EMBEDDINGS}'"
                )
            return success

        except Exception as e:
            self.logger.error(f"Failed to send chunks to queue: {str(e)}")
            return False

    async def ingest(
        self, file: UploadFile, splitter_type: str, chunk_size: int, chunk_overlap: int
    ) -> IngestResponse:
        file_id = str(uuid.uuid4())

        try:
            chunks = await self.document_service.process_document(
                file, splitter_type, chunk_size, chunk_overlap
            )

            await self.send_chunks_to_queue(file_id, chunks)
            self.logger.info(
                f"File {file.filename} ingested successfully. "
                f"Chunks sent to queue '{settings.KAFKA_TOPIC_EMBEDDINGS}'"
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
            self.logger.exception(f"Error processing file: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to process file: {str(e)}",
            )
