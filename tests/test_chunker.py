from rag_ingestor.ingestion.chunker import chunk_text


def test_chunk_text_empty():
    """Test chunking with empty text"""
    chunks = chunk_text("")
    assert chunks == []
