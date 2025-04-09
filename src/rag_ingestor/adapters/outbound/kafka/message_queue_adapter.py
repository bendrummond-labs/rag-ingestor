import json
import logging
import uuid
from typing import Dict, Any, List, Optional

from aiokafka import AIOKafkaProducer
from datetime import datetime

from rag_ingestor.ports.outbound.message_queue_port import MessageQueuePort
from rag_ingestor.domain.model import ContentChunk

logger = logging.getLogger(__name__)


class KafkaMessageQueueAdapter(MessageQueuePort):
    """
    Kafka message queue adapter for publishing content chunks and events.
    """

    def __init__(
        self,
        bootstrap_servers: str,
        chunks_topic: str = "document-chunks",
        events_topic: str = "system-events",
    ):
        """
        Initialize the Kafka producer.

        Args:
            bootstrap_servers: Comma-separated list of Kafka bootstrap servers.
            chunks_topic: Topic name for document chunks.
            events_topic: Topic name for document events.
        """
        self.bootstrap_servers = bootstrap_servers
        self.chunks_topic = chunks_topic
        self.events_topic = events_topic
        self.producer = None

    async def initialize(self):
        """
        Initialize the Kafka producer.
        """
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            key_serializer=lambda k: str(k).encode("utf-8"),
        )
        await self.producer.start()
        logger.info(f"Connected to Kafka at {self.bootstrap_servers}")

    async def publish_chunks(
        self, chunks: List[ContentChunk], metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Publish document chunks to the Kafka topic.

        Args:
            chunks: List of ContentChunk objects to publish
            metadata: Optional metadata to attach to the message

        Returns:
            Dictionary containing information about the publish operation
        """
        if not self.producer:
            raise RuntimeError(
                "Kafka producer not initialized. Call initialize() first."
            )

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

        # Publish each chunk as a separate message with the parent doc ID as key
        results = []
        for chunk in chunks:
            # Convert chunk to dictionary for serialization
            chunk_data = chunk.to_dict()

            # Add metadata to the message
            message = {"chunk": chunk_data, "metadata": message_metadata}

            # Use content_id as the message key for partitioning
            key = str(chunk.content_id)

            # Send the message
            try:
                result = await self.producer.send_and_wait(
                    self.chunks_topic, value=message, key=key
                )
                results.append(result)
                logger.debug(f"Published chunk {chunk.id} to {self.chunks_topic}")
            except Exception as e:
                logger.error(f"Error publishing chunk {chunk.id}: {str(e)}")
                raise

        return {
            "status": "success",
            "message": f"Published {len(results)} chunks",
            "topic": self.chunks_topic,
            "batch_id": message_metadata["batch_id"],
            "count": len(results),
        }

    async def publish_event(
        self, event_type: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Publish an event to the Kafka topic.

        Args:
            event_type: Type of event (e.g., 'document.processed', 'chunk.created')
            payload: Event data to publish

        Returns:
            Dictionary containing information about the publish operation
        """
        if not self.producer:
            raise RuntimeError(
                "Kafka producer not initialized. Call initialize() first."
            )

        # Prepare the event message
        event_id = str(uuid.uuid4())
        message = {
            "event_id": event_id,
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "payload": payload,
        }

        # Use event_type as the message key for partitioning
        key = event_type

        # Send the message
        try:
            result = await self.producer.send_and_wait(
                self.events_topic, value=message, key=key
            )
            logger.debug(f"Published event {event_id} to {self.events_topic}")
            logger.debug(f"Event details: {result}")
            return {
                "status": "success",
                "message": f"Published event {event_id}",
                "topic": self.events_topic,
                "event_id": event_id,
                "event_type": event_type,
            }
        except Exception as e:
            logger.error(f"Error publishing event {event_id}: {str(e)}")
            raise

    async def close(self) -> None:
        """
        Close the connection to Kafka.

        This method should be called when shutting down the application to ensure
        that all resources are properly released.
        """
        if self.producer:
            await self.producer.stop()
            logger.info("Disconnected from Kafka")
