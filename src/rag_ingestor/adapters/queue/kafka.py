import logging
import datetime
from typing import Any, Dict, ClassVar

from rag_ingestor.config import settings
from rag_ingestor.services.kafka_service import KafkaService
from rag_ingestor.adapters.queue.base import MessageQueue

logger = logging.getLogger(__name__)


class KafkaMessageQueue(MessageQueue):
    """Kafka implementation of the MessageQueue interface"""

    _instances: ClassVar[Dict[str, "KafkaMessageQueue"]] = {}

    @classmethod
    def get_instance(cls) -> "KafkaMessageQueue":
        """
        Get singleton instance of the Kafka message queue

        Returns:
            KafkaMessageQueue: Singleton instance
        """
        if "default" not in cls._instances:
            instance = cls()
            cls._instances["default"] = instance

        return cls._instances["default"]

    @classmethod
    async def shutdown_all(cls) -> None:
        """Shutdown all Kafka message queue instances"""
        for instance in cls._instances.values():
            await instance.shutdown()

        cls._instances.clear()

    async def initialize(self) -> None:
        """Nothing to initialize as producers are created per-topic in send_message"""
        logger.info("Kafka message queue initialized")

    async def shutdown(self) -> None:
        """Shutdown all Kafka producers"""
        try:
            await KafkaService.shutdown_all()
            logger.info("Kafka message queue shutdown complete")
        except Exception as e:
            logger.error(f"Error shutting down Kafka message queue: {e}")

    async def send_message(self, queue_name: str, message: Dict[str, Any]) -> bool:
        """
        Send a message to a Kafka topic

        Args:
            queue_name: Kafka topic name
            message: Message payload

        Returns:
            bool: True if successful, False otherwise
        """
        if not settings.ENABLE_KAFKA:
            logger.warning(
                f"Kafka disabled, message to {queue_name} not sent: {message}"
            )
            return False

        try:
            # Get or create a producer for this topic
            producer = await KafkaService.get_instance(topic=queue_name)

            # Add timestamp if not present
            if "timestamp" not in message:
                message["timestamp"] = datetime.datetime.now().isoformat()

            # Send message
            await producer.send(message)
            logger.info(f"Sent message to Kafka topic '{queue_name}'")
            return True

        except Exception as e:
            logger.error(f"Failed to send message to Kafka topic '{queue_name}': {e}")
            return False
