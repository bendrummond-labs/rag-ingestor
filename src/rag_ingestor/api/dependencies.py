"""
FastAPI dependency injection utilities for the RAG ingestor API.

This module provides functions that create and configure the components needed
by API endpoints, using FastAPI's dependency injection system.
"""

from functools import lru_cache
from typing import Dict, Any, Optional

from fastapi import Depends
from pydantic_settings import BaseSettings


from rag_ingestor.adapters.outbound import (
    InMemoryMessageQueueAdapter,
    LangchainDocumentLoaderAdapter,
    LangchainTextChunkingAdapter,
    KafkaMessageQueueAdapter,
)
from rag_ingestor.ports.outbound.message_queue_port import MessageQueuePort
from rag_ingestor.application.services import DocumentService


class Settings(BaseSettings):
    """Application settings."""

    # Message queue settings
    message_queue_type: str = "kafka"  # Options: "kafka", "inmemory"
    kafka_bootstrap_servers: str = "localhost:19092"
    kafka_chunks_topic: str = "document-chunks"
    kafka_events_topic: str = "system-events"

    # Chunking settings
    chunking_enabled: bool = True
    chunking_splitter_type: str = "recursive_character"
    chunking_chunk_size: int = 1000
    chunking_chunk_overlap: int = 200

    class Config:
        env_prefix = "RAG_"
        env_file = ".env"


@lru_cache
def get_settings():
    """
    Get application settings from environment variables.

    Returns:
        Settings object
    """
    return Settings()


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


async def get_message_queue(
    settings: Settings = Depends(get_settings),
) -> MessageQueuePort:
    """
    Create and configure a message queue adapter.

    Args:
        settings: Application settings

    Returns:
        Configured MessageQueuePort implementation
    """
    if settings.message_queue_type == "kafka":
        adapter = KafkaMessageQueueAdapter(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            chunks_topic=settings.kafka_chunks_topic,
            events_topic=settings.kafka_events_topic,
        )
        await adapter.initialize()
        return adapter
    else:
        # Default to in-memory for testing and development
        return InMemoryMessageQueueAdapter()


def get_document_service(
    chunking_enabled: bool = DEFAULT_CONFIG["chunking"]["enabled"],
    chunking_config: Optional[Dict[str, Any]] = None,
    message_queue: Optional[MessageQueuePort] = None,
):
    """
    Create and configure a document service.

    Args:
        chunking_enabled: Whether to enable text chunking
        chunking_config: Custom configuration for text chunking
        message_queue: Optional message queue for publishing events

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
    return DocumentService(
        document_loader=document_loader,
        text_chunker=text_chunker,
        message_queue=message_queue,
    )
