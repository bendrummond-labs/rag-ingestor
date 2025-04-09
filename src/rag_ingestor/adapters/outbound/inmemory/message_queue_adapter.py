"""
In-memory message queue adapter for the RAG ingestor.

This module provides an implementation of the MessageQueuePort that stores
messages in memory, primarily for testing purposes.
"""

import logging
import uuid
from collections import defaultdict
from typing import Dict, Any, List, Optional, DefaultDict
from datetime import datetime

from rag_ingestor.ports.outbound.message_queue_port import MessageQueuePort
from rag_ingestor.domain.model import ContentChunk

logger = logging.getLogger(__name__)


class InMemoryMessageQueueAdapter(MessageQueuePort):
    """
    Implementation of MessageQueuePort using in-memory storage.

    This adapter provides methods to store messages in memory, which is useful
    for testing and development without requiring an external message broker.

    Attributes:
        chunks_messages: Dictionary of lists containing published chunk messages
        event_messages: Dictionary of lists containing published event messages
    """

    def __init__(self):
        """Initialize the in-memory message queue adapter."""
        # Store messages by topic
        self.chunks_messages: DefaultDict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.event_messages: DefaultDict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.is_closed = False
        logger.info("Initialized in-memory message queue adapter")

    async def publish_chunks(
        self, chunks: List[ContentChunk], metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Store document chunks in memory.

        Args:
            chunks: List of ContentChunk objects to publish
            metadata: Optional metadata to attach to the message

        Returns:
            Dictionary containing information about the operation
        """
        if self.is_closed:
            raise RuntimeError("Message queue is closed")

        if not chunks:
            logger.warning("No chunks provided to publish_chunks")
            return {"status": "warning", "message": "No chunks provided", "count": 0}

        # Prepare metadata with defaults
        message_metadata = {
            "timestamp": datetime.now().isoformat(),
            "batch_id": str(uuid.uuid4()),
        }

        if metadata:
            message_metadata.update(metadata)

        # Group chunks by content_id to simulate Kafka's partitioning
        content_groups: DefaultDict[str, List[Dict[str, Any]]] = defaultdict(list)

        for chunk in chunks:
            # Convert chunk to dictionary
            chunk_data = chunk.to_dict()

            # Add message metadata
            message = {"chunk": chunk_data, "metadata": message_metadata}

            # Group by content_id
            content_id = str(chunk.content_id)
            content_groups[content_id].append(message)

        # Store the grouped messages
        for content_id, messages in content_groups.items():
            topic_key = f"document-chunks-{content_id}"
            self.chunks_messages[topic_key].extend(messages)

        # Store all messages in a common topic
        self.chunks_messages["document-chunks"].extend(
            [msg for msgs in content_groups.values() for msg in msgs]
        )

        total_messages = sum(len(msgs) for msgs in content_groups.values())
        logger.debug(f"Stored {total_messages} chunk messages in memory")

        return {
            "status": "success",
            "message": f"Stored {total_messages} chunks",
            "topic": "document-chunks",
            "batch_id": message_metadata["batch_id"],
            "count": total_messages,
        }

    async def publish_event(
        self, event_type: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Store an event in memory.

        Args:
            event_type: Type of event (e.g., 'document.processed', 'chunk.created')
            payload: Event data to publish

        Returns:
            Dictionary containing information about the operation
        """
        if self.is_closed:
            raise RuntimeError("Message queue is closed")

        # Prepare the event message
        event_id = str(uuid.uuid4())
        message = {
            "event_id": event_id,
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "payload": payload,
        }

        # Store the event message
        self.event_messages["system-events"].append(message)

        # Also store by event type
        self.event_messages[f"event-{event_type}"].append(message)

        logger.debug(f"Stored event {event_id} in memory")

        return {
            "status": "success",
            "message": f"Stored event {event_id}",
            "event_id": event_id,
            "event_type": event_type,
        }

    async def close(self) -> None:
        """Mark the queue as closed."""
        self.is_closed = True
        logger.info("Closed in-memory message queue")

    # Testing-specific methods

    def get_chunks(self, topic: str = "document-chunks") -> List[Dict[str, Any]]:
        """
        Get all chunks stored for a topic.

        Args:
            topic: Topic name to retrieve chunks from

        Returns:
            List of stored chunk messages
        """
        return self.chunks_messages.get(topic, [])

    def get_events(self, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get events, optionally filtered by type.

        Args:
            event_type: Optional event type to filter by

        Returns:
            List of stored event messages
        """
        if event_type:
            return self.event_messages.get(f"event-{event_type}", [])
        return self.event_messages.get("system-events", [])

    def clear(self) -> None:
        """Clear all stored messages."""
        self.chunks_messages.clear()
        self.event_messages.clear()
        logger.debug("Cleared all stored messages")
