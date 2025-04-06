import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import tempfile
import os

from rag_ingestor.adapters.loaders import (
    BaseDocumentLoader,
    TextLoader,
    PDFLoader,
    CSVLoader,
    LoaderManager,
)
from langchain_core.documents import Document


class TestLoaderManager:
    """Tests for the LoaderManager class."""

    def test_register_loader(self):
        """Test registering loaders."""
        manager = LoaderManager()
        mock_loader = Mock(spec=BaseDocumentLoader)

        # Register a loader
        manager.register_loader(".txt", mock_loader)

        # Verify it was registered
        assert ".txt" in manager.loaders
        assert manager.loaders[".txt"] == mock_loader

    def test_get_loader(self):
        """Test getting registered loaders."""
        manager = LoaderManager()
        mock_loader = Mock(spec=BaseDocumentLoader)

        # Register a loader
        manager.register_loader(".pdf", mock_loader)

        # Get the loader
        loader = manager.get_loader(".pdf")
        assert loader == mock_loader

        # Try to get a non-existent loader
        assert manager.get_loader(".docx") is None

    def test_load_document_valid_extension(self):
        """Test loading a document with a valid extension."""
        manager = LoaderManager()
        mock_loader = Mock(spec=BaseDocumentLoader)
        mock_loader.load.return_value = [
            Document(page_content="Test content", metadata={})
        ]

        # Register the loader
        manager.register_loader(".txt", mock_loader)

        # Load a document
        docs = manager.load_document("test.txt")

        # Verify the loader was called
        mock_loader.load.assert_called_once_with("test.txt")

        # Verify the result
        assert len(docs) == 1
        assert docs[0].page_content == "Test content"

    def test_load_document_invalid_extension(self):
        """Test loading a document with an invalid extension."""
        manager = LoaderManager()

        # Try to load a document with unregistered extension
        with pytest.raises(ValueError) as exc_info:
            manager.load_document("test.docx")

        # Verify the error message
        assert "Unsupported file type" in str(exc_info.value)


class TestTextLoader:
    """Tests for the TextLoader class."""

    def test_load_text_file(self, temp_text_file: Path):
        """Test loading a text file."""
        loader = TextLoader()

        # Load the document
        docs = loader.load(str(temp_text_file))

        # Verify the document was loaded
        assert isinstance(docs, list)
        assert len(docs) > 0
        assert isinstance(docs[0], Document)

        # Check content was loaded correctly
        with open(temp_text_file, "r", encoding="utf-8") as f:
            expected_content = f.read().strip()
        assert docs[0].page_content.strip() == expected_content

    def test_load_nonexistent_file(self):
        """Test loading a non-existent file."""
        loader = TextLoader()

        # Try to load a non-existent file
        with pytest.raises(Exception):
            loader.load("nonexistent_file.txt")


class TestCSVLoader:
    """Tests for the CSVLoader class."""

    @pytest.fixture
    def temp_csv_file(self) -> Path:
        """Create a temporary CSV file for testing."""
        csv_content = "name,age,city\nJohn,30,New York\nJane,25,San Francisco\n"

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as temp_file:
            temp_file.write(csv_content.encode("utf-8"))
            temp_path = Path(temp_file.name)

        yield temp_path

        # Cleanup
        if temp_path.exists():
            os.unlink(temp_path)

    def test_load_csv_file(self, temp_csv_file: Path):
        """Test loading a CSV file."""
        loader = CSVLoader()

        # Load the document
        docs = loader.load(str(temp_csv_file))

        # Verify the document was loaded
        assert isinstance(docs, list)
        assert len(docs) > 0
        assert isinstance(docs[0], Document)

        # Check content was loaded correctly
        assert "name" in docs[0].page_content
        assert "John" in docs[0].page_content


class TestPDFLoader:
    """Tests for the PDFLoader class."""

    def test_load_pdf_file(self):
        """Test PDF loader by mocking the LangChain loader."""
        # Since creating actual PDF files is complex, we'll mock the underlying loader
        with patch(
            "rag_ingestor.adapters.loaders.pdf_loader.UnstructuredPDFLoader"
        ) as mock_loader_cls:
            # Setup the mock to return a document
            mock_loader = Mock()
            mock_loader.load.return_value = [
                Document(page_content="PDF content", metadata={})
            ]
            mock_loader_cls.return_value = mock_loader

            # Create our loader
            loader = PDFLoader()

            # Load a document
            docs = loader.load("test.pdf")

            # Verify the mock was called
            mock_loader_cls.assert_called_once_with("test.pdf")
            mock_loader.load.assert_called_once()

            # Verify the result
            assert len(docs) == 1
            assert docs[0].page_content == "PDF content"
