from rag_ingestor.ingestion.chunker import chunk_text


def test_chunk_text_empty():
    """Test chunking with empty text"""

    chunks = chunk_text("")
    assert chunks == []


def test_chunk_text_small():
    """Test chunking with text smaller than chunk size"""
    text = "This is a small text"
    chunks = chunk_text(text, chunk_size=500)
    assert len(chunks) == 1
    assert chunks[0] == text
