import pytest
from unittest.mock import patch
from pathlib import Path
from fastapi import HTTPException, UploadFile

from rag_ingestor.services.document_service import DocumentService
from rag_ingestor.adapters.loaders import LoaderManager
from rag_ingestor.adapters.splitters import SplitterManager
from langchain_core.documents import Document


class TestDocumentService:
    def test_validate_file_type_valid(
        self, loader_manager: LoaderManager, splitter_manager: SplitterManager
    ):
        """Test that valid file types are accepted."""
        service = DocumentService(loader_manager, splitter_manager)

        # Should not raise for valid extensions
        service.validate_file_type(".txt")
        service.validate_file_type(".pdf")
        service.validate_file_type(".csv")

    def test_validate_file_type_invalid(
        self, loader_manager: LoaderManager, splitter_manager: SplitterManager
    ):
        """Test that invalid file types are rejected."""
        service = DocumentService(loader_manager, splitter_manager)

        # Should raise for invalid extensions
        with pytest.raises(HTTPException) as exc_info:
            service.validate_file_type(".docx")

        assert exc_info.value.status_code == 415
        assert "Unsupported file type" in exc_info.value.detail

    def test_validate_chunking_parameters_valid(
        self, document_service: DocumentService
    ):
        """Test that valid chunking parameters are accepted."""
        # Should not raise for valid chunking parameters
        document_service.validate_chunking_parameters(100, 50)

    def test_validate_chunking_parameters_invalid(
        self, document_service: DocumentService
    ):
        """Test that invalid chunking parameters are rejected."""
        # Should raise when chunk_overlap >= chunk_size
        with pytest.raises(HTTPException) as exc_info:
            document_service.validate_chunking_parameters(100, 100)

        assert exc_info.value.status_code == 400
        assert "chunk_overlap must be less than chunk_size" in exc_info.value.detail

        with pytest.raises(HTTPException) as exc_info:
            document_service.validate_chunking_parameters(100, 120)

        assert exc_info.value.status_code == 400

    def test_read_file_contents(
        self, document_service: DocumentService, mock_upload_file: UploadFile
    ):
        """Test reading file contents."""
        # Read the file contents
        contents = document_service.read_file_contents(mock_upload_file)

        # Verify contents were read correctly
        assert isinstance(contents, bytes)
        assert len(contents) > 0

        # Verify file pointer was reset
        assert mock_upload_file.file.tell() == 0

    def test_read_file_contents_too_large(
        self, document_service: DocumentService, mock_upload_file: UploadFile
    ):
        """Test reading file that's too large."""
        # Patch the MAX_FILE_SIZE to be very small
        with patch("rag_ingestor.services.document_service.settings.MAX_FILE_SIZE", 10):
            with pytest.raises(HTTPException) as exc_info:
                document_service.read_file_contents(mock_upload_file)

            assert exc_info.value.status_code == 413
            assert "File too large" in exc_info.value.detail

    def test_load_document(
        self, document_service: DocumentService, temp_text_file: Path
    ):
        """Test loading a document."""
        # Read file contents
        with open(temp_text_file, "rb") as f:
            contents = f.read()

        # Load the document
        documents = document_service.load_document(contents, ".txt")

        # Verify documents were loaded
        assert isinstance(documents, list)
        assert len(documents) > 0
        assert isinstance(documents[0], Document)

    def test_split_document(self, document_service: DocumentService):
        """Test splitting a document."""
        # Create test documents
        docs = [
            Document(
                page_content="This is test document 1. It should be split into chunks.",
                metadata={"source": "test1.txt"},
            ),
            Document(
                page_content="This is test document 2. It also should be split.",
                metadata={"source": "test2.txt"},
            ),
        ]

        # Split the documents
        chunks = document_service.split_document(docs, "plain", 20, 5)

        # Verify chunks were created
        assert isinstance(chunks, list)
        assert len(chunks) > 2  # Should have more chunks than original docs

        # Verify chunk structure
        for chunk in chunks:
            assert "page_content" in chunk
            assert "metadata" in chunk
            assert isinstance(chunk["page_content"], str)
            assert isinstance(chunk["metadata"], dict)

    def test_split_document_invalid_splitter(self, document_service: DocumentService):
        """Test splitting with invalid splitter type."""
        docs = [Document(page_content="Test", metadata={})]

        with pytest.raises(HTTPException) as exc_info:
            document_service.split_document(docs, "nonexistent", 100, 20)

        assert exc_info.value.status_code == 400
        assert "Invalid splitter configuration" in exc_info.value.detail
