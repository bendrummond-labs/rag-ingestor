import os
import pytest
import tempfile
from unittest.mock import Mock
from pathlib import Path
from typing import Generator, AsyncGenerator
from fastapi import UploadFile
from fastapi.testclient import TestClient

# Import your application components
from rag_ingestor.adapters.loaders import (
    LoaderManager,
    TextLoader,
    PDFLoader,
    CSVLoader,
)
from rag_ingestor.adapters.splitters import (
    SplitterManager,
    PlainTextSplitter,
    MarkdownSplitter,
)
from rag_ingestor.adapters.queue.memory import InMemoryMessageQueue
from rag_ingestor.services.document_service import DocumentService
from rag_ingestor.services.ingestion_service import IngestionService
from rag_ingestor.di_container import DIContainer, container
from rag_ingestor.main import app as main_app
from rag_ingestor.config import Settings


# Create a test settings object with controlled values
@pytest.fixture
def test_settings() -> Settings:
    """Test settings with controlled values."""
    settings = Settings(
        MAX_FILE_SIZE=1024 * 1024,  # 1MB
        ENABLE_KAFKA=False,  # Use in-memory queue for tests
        DEFAULT_CHUNK_SIZE=100,
        DEFAULT_CHUNK_OVERLAP=20,
    )
    return settings


# Fixture for sample text content
@pytest.fixture
def sample_text() -> str:
    """Sample text for testing."""
    return """
    This is a sample text document.
    It has multiple lines.
    
    And even some paragraph breaks.
    This should be enough to create multiple chunks.
    """


# Fixture for creating a temporary text file
@pytest.fixture
def temp_text_file(sample_text: str) -> Generator[Path, None, None]:
    """Create a temporary text file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_file:
        temp_file.write(sample_text.encode("utf-8"))
        temp_path = Path(temp_file.name)

    yield temp_path

    # Cleanup
    if temp_path.exists():
        os.unlink(temp_path)


# Fixture for mocking an uploaded file
@pytest.fixture
def mock_upload_file(sample_text: str) -> Generator[UploadFile, None, None]:
    """Create a mock UploadFile for testing."""
    # Create a temporary file and build a mock around it
    with tempfile.NamedTemporaryFile(suffix=".txt") as temp_file:
        temp_file.write(sample_text.encode("utf-8"))
        temp_file.flush()
        temp_file.seek(0)

        # Create a mock UploadFile that behaves like FastAPI's UploadFile
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = f"test_file_{os.path.basename(temp_file.name)}"
        mock_file.file = temp_file
        mock_file.content_type = "text/plain"

        yield mock_file


# Fixtures for core components


@pytest.fixture
def loader_manager() -> LoaderManager:
    """Create a pre-configured loader manager."""
    manager = LoaderManager()
    manager.register_loader(".txt", TextLoader())
    manager.register_loader(".md", TextLoader())
    manager.register_loader(".pdf", PDFLoader())
    manager.register_loader(".csv", CSVLoader())
    return manager


@pytest.fixture
def splitter_manager() -> SplitterManager:
    """Create a pre-configured splitter manager."""
    manager = SplitterManager()
    manager.register_splitter("plain", PlainTextSplitter)
    manager.register_splitter("markdown", MarkdownSplitter)
    return manager


@pytest.fixture
async def message_queue() -> AsyncGenerator[InMemoryMessageQueue, None]:
    """Create and initialize an in-memory message queue."""
    queue = InMemoryMessageQueue()
    await queue.initialize()
    yield queue
    await queue.shutdown()


@pytest.fixture
def document_service(
    loader_manager: LoaderManager, splitter_manager: SplitterManager
) -> DocumentService:
    """Create a document service with test dependencies."""
    return DocumentService(
        loader_manager=loader_manager, splitter_manager=splitter_manager
    )


@pytest.fixture
async def ingestion_service(
    document_service: DocumentService, message_queue: InMemoryMessageQueue
) -> IngestionService:
    """Create an ingestion service with test dependencies."""
    return IngestionService(
        document_service=document_service, message_queue=message_queue
    )


# Test container with mocked dependencies


@pytest.fixture
async def test_container(
    loader_manager: LoaderManager,
    splitter_manager: SplitterManager,
    message_queue: InMemoryMessageQueue,
    document_service: DocumentService,
    ingestion_service: IngestionService,
) -> AsyncGenerator[DIContainer, None]:
    """Create a test container with controlled dependencies."""
    # Save original services
    original_services = container.services.copy()

    # Register test services
    container.register("loader_manager", loader_manager)
    container.register("splitter_manager", splitter_manager)
    container.register("message_queue", message_queue)
    container.register("document_service", document_service)
    container.register("ingestion_service", ingestion_service)

    yield container

    # Restore original services
    container.services = original_services


# FastAPI test client


@pytest.fixture
async def test_client(test_container: DIContainer) -> AsyncGenerator[TestClient, None]:
    """Create a FastAPI test client with test dependencies."""
    with TestClient(main_app) as client:
        yield client
