import pytest
from unittest.mock import Mock
from langchain_core.documents import Document

from rag_ingestor.adapters.splitters import (
    PlainTextSplitter,
    MarkdownSplitter,
    SplitterManager,
)
from rag_ingestor.adapters.splitters.base import TextSplitter


class TestSplitterManager:
    """Tests for the SplitterManager class."""

    def test_register_splitter(self):
        """Test registering splitters."""
        manager = SplitterManager()
        mock_splitter_cls = Mock(spec=type)

        # Register a splitter
        manager.register_splitter("test", mock_splitter_cls)

        # Verify it was registered
        assert "test" in manager.splitter_types
        assert manager.splitter_types["test"] == mock_splitter_cls

    def test_get_splitter(self):
        """Test getting a splitter instance."""
        manager = SplitterManager()
        mock_splitter = Mock(spec=TextSplitter)
        mock_splitter_cls = Mock(return_value=mock_splitter)

        # Register a splitter
        manager.register_splitter("test", mock_splitter_cls)

        # Get an instance
        splitter = manager.get_splitter("test", 100, 20)

        # Verify the factory was called with the right parameters
        mock_splitter_cls.assert_called_once_with(chunk_size=100, chunk_overlap=20)

        # Verify the result
        assert splitter == mock_splitter

    def test_get_splitter_invalid_type(self):
        """Test getting a non-existent splitter type."""
        manager = SplitterManager()

        # Try to get a non-existent splitter
        with pytest.raises(ValueError) as exc_info:
            manager.get_splitter("nonexistent", 100, 20)

        # Verify the error message
        assert "Unsupported splitter type" in str(exc_info.value)
        assert "nonexistent" in str(exc_info.value)


class TestPlainTextSplitter:
    """Tests for the PlainTextSplitter class."""

    def test_init(self):
        """Test initialization with custom parameters."""
        splitter = PlainTextSplitter(chunk_size=200, chunk_overlap=50)
        assert splitter.splitter._chunk_size == 200
        assert splitter.splitter._chunk_overlap == 50

    def test_split_documents(self):
        """Test splitting documents."""
        splitter = PlainTextSplitter(chunk_size=10, chunk_overlap=2)

        # Create test documents
        docs = [
            Document(
                page_content="This is a test document with more than 10 characters.",
                metadata={"source": "test.txt"},
            ),
            Document(
                page_content="Another test document for splitting.",
                metadata={"source": "test2.txt"},
            ),
        ]

        # Split the documents
        chunks = splitter.split_documents(docs)

        # Verify results
        assert len(chunks) > 2  # Should have split into more chunks

        # Verify chunk content
        for chunk in chunks:
            assert isinstance(chunk, Document)
            assert len(chunk.page_content) <= 12  # chunk_size + chunk_overlap

            # Check metadata was preserved
            assert "source" in chunk.metadata
            assert chunk.metadata["source"] in ["test.txt", "test2.txt"]


class TestMarkdownSplitter:
    """Tests for the MarkdownSplitter class."""

    def test_init(self):
        """Test initialization with custom parameters."""
        splitter = MarkdownSplitter(chunk_size=200, chunk_overlap=50)
        assert splitter.splitter._chunk_size == 200
        assert splitter.splitter._chunk_overlap == 50

    def test_split_documents(self):
        """Test splitting markdown documents."""
        splitter = MarkdownSplitter(chunk_size=20, chunk_overlap=5)

        # Create test markdown documents
        docs = [
            Document(
                page_content="# Header\n\nThis is a markdown document with headers.\n\n## Subheader\n\nAnd some more content.",
                metadata={"source": "test.md"},
            ),
        ]

        # Split the documents
        chunks = splitter.split_documents(docs)

        # Verify results
        assert len(chunks) > 1  # Should have split into chunks

        # Check if the markdown-aware splitting happened (headers should be respected where possible)
        has_header = False
        has_subheader = False

        for chunk in chunks:
            if "# Header" in chunk.page_content:
                has_header = True
            if "## Subheader" in chunk.page_content:
                has_subheader = True

            # Check metadata was preserved
            assert chunk.metadata["source"] == "test.md"

        # At least one of the chunks should contain a header
        assert has_header or has_subheader
