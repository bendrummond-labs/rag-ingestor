"""
FastAPI dependency injection utilities for the RAG ingestor API.

This module provides functions that create and configure the components needed
by API endpoints, using FastAPI's dependency injection system.
"""

from functools import lru_cache
from typing import Dict, Any, Optional

from rag_ingestor.application.services import DocumentService
from rag_ingestor.adapters.outbound.langchain.document_loader_adapter import (
    LangchainDocumentLoaderAdapter,
)
from rag_ingestor.adapters.outbound.langchain.text_chunking_adapter import (
    LangchainTextChunkingAdapter,
)


# Default configuration
DEFAULT_CONFIG = {
    "chunking": {
        "enabled": True,
        "splitter_type": "recursive_character",
        "chunk_size": 1000,
        "chunk_overlap": 200,
    }
}


@lru_cache
def get_document_loader_adapter():
    """
    Create and configure a document loader adapter.

    Returns:
        Configured LangchainDocumentLoaderAdapter
    """
    return LangchainDocumentLoaderAdapter()


@lru_cache
def get_text_chunking_adapter(
    splitter_type: str = DEFAULT_CONFIG["chunking"]["splitter_type"],
    chunk_size: int = DEFAULT_CONFIG["chunking"]["chunk_size"],
    chunk_overlap: int = DEFAULT_CONFIG["chunking"]["chunk_overlap"],
    **kwargs,
):
    """
    Create and configure a text chunking adapter.

    Args:
        splitter_type: Type of text splitter to use
        chunk_size: Size of text chunks
        chunk_overlap: Overlap between chunks
        **kwargs: Additional parameters for the text splitter

    Returns:
        Configured LangchainTextChunkingAdapter
    """
    return LangchainTextChunkingAdapter(
        splitter_type=splitter_type,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        **kwargs,
    )


def get_document_service(
    chunking_enabled: bool = DEFAULT_CONFIG["chunking"]["enabled"],
    chunking_config: Optional[Dict[str, Any]] = None,
):
    """
    Create and configure a document service.

    Args:
        chunking_enabled: Whether to enable text chunking
        chunking_config: Custom configuration for text chunking

    Returns:
        Configured DocumentService
    """
    # Create document loader adapter
    document_loader = get_document_loader_adapter()

    # Create text chunker if enabled
    text_chunker = None
    if chunking_enabled:
        # Use custom config if provided, otherwise use defaults
        config = chunking_config or DEFAULT_CONFIG["chunking"]
        text_chunker = get_text_chunking_adapter(
            splitter_type=config.get(
                "splitter_type", DEFAULT_CONFIG["chunking"]["splitter_type"]
            ),
            chunk_size=config.get(
                "chunk_size", DEFAULT_CONFIG["chunking"]["chunk_size"]
            ),
            chunk_overlap=config.get(
                "chunk_overlap", DEFAULT_CONFIG["chunking"]["chunk_overlap"]
            ),
        )

    # Create and return service
    return DocumentService(document_loader=document_loader, text_chunker=text_chunker)
