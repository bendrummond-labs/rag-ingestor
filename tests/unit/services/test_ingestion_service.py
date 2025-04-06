import pytest
from unittest.mock import Mock, AsyncMock
from fastapi import UploadFile, HTTPException

from rag_ingestor.services.ingestion_service import IngestionService
from rag_ingestor.services.document_service import DocumentService
from rag_ingestor.adapters.queue.memory import InMemoryMessageQueue
from rag_ingestor.config import settings


@pytest.mark.asyncio
class TestIngestionService:
    """Unit tests for IngestionService"""

    async def test_send_chunks_to_queue(self, message_queue: InMemoryMessageQueue):
        """Test sending chunks to the message queue."""
        # Create a mock document service
        mock_doc_service = Mock(spec=DocumentService)

        # Create the ingestion service
        service = IngestionService(
            document_service=mock_doc_service, message_queue=message_queue
        )

        # Create test chunks
        file_id = "test-file-id"
        chunks = [
            {"page_content": "Chunk 1", "metadata": {"source": "test.txt"}},
            {"page_content": "Chunk 2", "metadata": {"source": "test.txt"}},
        ]

        # Send chunks to queue
        result = await service.send_chunks_to_queue(file_id, chunks)

        # Verify result
        assert result is True

        # Verify message was sent to the queue
        messages = message_queue.get_messages(settings.KAFKA_TOPIC_EMBEDDINGS)
        assert len(messages) == 1
        assert messages[0]["file_id"] == file_id
        assert messages[0]["documents"] == chunks

    async def test_send_chunks_to_queue_failure(self):
        """Test handling failure when sending to queue."""
        # Create mocks
        mock_doc_service = Mock(spec=DocumentService)
        mock_queue = AsyncMock(spec=InMemoryMessageQueue)
        mock_queue.send_message.return_value = False

        # Create the ingestion service
        service = IngestionService(
            document_service=mock_doc_service, message_queue=mock_queue
        )

        # Attempt to send chunks with a failing queue
        result = await service.send_chunks_to_queue(
            "test-id", [{"page_content": "Test"}]
        )

        # Verify result
        assert result is False

        # Verify the queue was called
        mock_queue.send_message.assert_called_once()

    async def test_ingest_success(
        self, message_queue: InMemoryMessageQueue, mock_upload_file: UploadFile
    ):
        """Test successful document ingestion."""
        # Create mock document service that returns predictable chunks
        mock_doc_service = AsyncMock(spec=DocumentService)
        test_chunks = [
            {"page_content": "Test chunk 1", "metadata": {"source": "test.txt"}},
            {"page_content": "Test chunk 2", "metadata": {"source": "test.txt"}},
        ]
        mock_doc_service.process_document.return_value = test_chunks

        # Create the ingestion service
        service = IngestionService(
            document_service=mock_doc_service, message_queue=message_queue
        )

        # Process the document
        response = await service.ingest(
            file=mock_upload_file,
            splitter_type="plain",
            chunk_size=100,
            chunk_overlap=20,
        )

        # Verify the document service was called
        mock_doc_service.process_document.assert_called_once_with(
            mock_upload_file, "plain", 100, 20
        )

        # Verify the response
        assert response.status == "processing"
        assert response.file_id is not None
        assert response.num_chunks == 2

        # Verify message was sent to queue
        messages = message_queue.get_messages(settings.KAFKA_TOPIC_EMBEDDINGS)
        assert len(messages) == 1
        assert messages[0]["file_id"] == response.file_id
        assert messages[0]["documents"] == test_chunks

    async def test_ingest_document_service_error(
        self, message_queue: InMemoryMessageQueue, mock_upload_file: UploadFile
    ):
        """Test handling errors from document service during ingestion."""
        # Create mock document service that raises an exception
        mock_doc_service = AsyncMock(spec=DocumentService)
        mock_doc_service.process_document.side_effect = HTTPException(
            status_code=400, detail="Test error"
        )

        # Create the ingestion service
        service = IngestionService(
            document_service=mock_doc_service, message_queue=message_queue
        )

        # Attempt to process the document, should re-raise the HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await service.ingest(
                file=mock_upload_file,
                splitter_type="plain",
                chunk_size=100,
                chunk_overlap=20,
            )

        # Verify the exception
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Test error"

        # Verify no messages were sent to queue
        assert len(message_queue.get_messages(settings.KAFKA_TOPIC_EMBEDDINGS)) == 0

    async def test_ingest_generic_error(
        self, message_queue: InMemoryMessageQueue, mock_upload_file: UploadFile
    ):
        """Test handling generic errors during ingestion."""
        # Create mock document service that raises a generic exception
        mock_doc_service = AsyncMock(spec=DocumentService)
        mock_doc_service.process_document.side_effect = ValueError(
            "Some internal error"
        )

        # Create the ingestion service
        service = IngestionService(
            document_service=mock_doc_service, message_queue=message_queue
        )

        # Attempt to process the document, should convert to HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await service.ingest(
                file=mock_upload_file,
                splitter_type="plain",
                chunk_size=100,
                chunk_overlap=20,
            )

        # Verify the exception was properly converted
        assert exc_info.value.status_code == 400
        assert "Failed to process file" in exc_info.value.detail

        # Verify no messages were sent to queue
        assert len(message_queue.get_messages(settings.KAFKA_TOPIC_EMBEDDINGS)) == 0
