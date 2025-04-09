import pytest

from rag_ingestor.adapters.outbound.langchain.text_chunking_adapter import (
    LangchainTextChunkingAdapter,
)
from rag_ingestor.domain.model import Content


@pytest.fixture
def sample_content():
    """Create a sample content for testing chunking."""
    paragraphs = [
        "This is paragraph one with some text. " * 5,
        "This is paragraph two with different content. " * 5,
        "This is paragraph three with even more text to process. " * 5,
        "This is paragraph four which should be in a different chunk. " * 5,
        "This is paragraph five with the final text for our test. " * 5,
    ]

    text = "\n\n".join(paragraphs)
    metadata = {
        "source": "test_document.txt",
        "language": "en",
        "author": "Test Author",
    }

    return Content(text=text, metadata=metadata)


def test_recursive_character_chunking(sample_content):
    """Test chunking with RecursiveCharacterTextSplitter."""
    adapter = LangchainTextChunkingAdapter(
        splitter_type="recursive_character", chunk_size=200, chunk_overlap=20
    )

    chunks = adapter.chunk_content(sample_content)

    assert len(chunks) > 1

    for chunk in chunks:
        assert chunk.content_id == sample_content.id

    for i, chunk in enumerate(chunks):
        assert chunk.sequence_number == i

    for chunk in chunks:
        assert chunk.metadata.source == "test_document.txt"
        assert chunk.metadata.language == "en"
        assert chunk.metadata.author == "Test Author"
        assert "chunk_index" in chunk.metadata.custom_metadata
        assert "total_chunks" in chunk.metadata.custom_metadata
        assert "parent_content_id" in chunk.metadata.custom_metadata
