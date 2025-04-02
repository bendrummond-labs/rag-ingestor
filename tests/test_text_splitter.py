from unittest.mock import patch
from enum import Enum

from rag_ingestor.ingestion.text_splitter import (
    get_text_splitter,
    SplitterType,
    SPLITTER_REGISTRY,
    logger,
)

# Sample test texts
SIMPLE_TEXT = (
    "This is a simple text. It has multiple sentences.\n\nWith some newlines too."
)
MARKDOWN_TEXT = "# Header\n\nSome markdown content\n\n## Subheader\nMore content"
PYTHON_CODE = "def hello():\n    print('world')\n\nclass Test:\n    pass"
HTML_TEXT = (
    "<html><h1>Title</h1><p>Content</p><h2>Subtitle</h2><p>More content</p></html>"
)


# Test parameters
TEST_CHUNK_SIZE = 100
TEST_CHUNK_OVERLAP = 20


class MockSplitterType(str, Enum):
    """Mock enum for testing invalid splitter types (renamed to avoid pytest collection)"""

    INVALID = "invalid"


def test_get_text_splitter_returns_correct_type():
    """Test that get_text_splitter returns the correct splitter type"""
    for splitter_type in SplitterType:
        splitter = get_text_splitter(splitter_type)
        assert isinstance(splitter, SPLITTER_REGISTRY[splitter_type])


def test_get_text_splitter_with_invalid_type_falls_back():
    """Test that invalid splitter types fall back to recursive"""
    with patch.object(logger, "warning") as mock_warning:
        splitter = get_text_splitter(MockSplitterType.INVALID)  # type: ignore
        assert isinstance(splitter, SPLITTER_REGISTRY[SplitterType.RECURSIVE])
        mock_warning.assert_called_once()
