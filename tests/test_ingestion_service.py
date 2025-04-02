import pytest
from fastapi import HTTPException
from rag_ingestor.services.ingestion_service import validate_chunking


def test_validate_chunking_passes():
    # Should not raise for valid inputs
    try:
        validate_chunking(chunk_size=500, chunk_overlap=100)
    except HTTPException:
        pytest.fail("validate_chunking raised an exception unexpectedly.")


def test_validate_chunking_raises_on_invalid():
    # Should raise when overlap >= chunk size
    with pytest.raises(HTTPException) as exc_info:
        validate_chunking(chunk_size=100, chunk_overlap=100)

    assert exc_info.value.status_code == 400
    assert "chunk_overlap must be less than chunk_size" in exc_info.value.detail
