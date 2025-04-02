import logging
import json
from typing import Any, Dict, ClassVar, Optional
from aiokafka import AIOKafkaProducer

from rag_ingestor.config import settings

logger = logging.getLogger(__name__)


class KafkaService:
    """Service for interacting with Kafka message broker"""

    # Class variable to store the singleton instances (one per topic)
    _instances: ClassVar[Dict[str, "KafkaService"]] = {}

    def __init__(self, topic: str):
        """
        Initialize a Kafka service for a specific topic

        Args:
            topic: The Kafka topic name
        """
        self.topic = topic
        self._producer: Optional[AIOKafkaProducer] = None
        self._started = False

    @classmethod
    async def get_instance(cls, topic: str) -> "KafkaService":
        """
        Get or create a Kafka service instance for a specific topic

        Args:
            topic: The Kafka topic name

        Returns:
            KafkaService: A Kafka service instance
        """
        if topic not in cls._instances:
            instance = cls(topic)
            cls._instances[topic] = instance
            await instance.start()

        return cls._instances[topic]

    @classmethod
    async def shutdown_all(cls) -> None:
        """Shutdown all Kafka service instances"""
        for instance in cls._instances.values():
            await instance.stop()

        cls._instances.clear()

    async def start(self) -> None:
        """Start the Kafka producer"""
        if self._started:
            return

        try:
            self._producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BROKER_URL,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
            await self._producer.start()
            self._started = True
            logger.info(
                f"Kafka producer started for topic '{self.topic}', "
                f"connected to {settings.KAFKA_BROKER_URL}"
            )
        except Exception as e:
            logger.error(
                f"Failed to start Kafka producer for topic '{self.topic}': {str(e)}"
            )
            raise

    async def stop(self) -> None:
        """Stop the Kafka producer"""
        if not self._started or not self._producer:
            return

        try:
            await self._producer.stop()
            self._started = False
            logger.info(f"Kafka producer stopped for topic '{self.topic}'")
        except Exception as e:
            logger.error(
                f"Error stopping Kafka producer for topic '{self.topic}': {str(e)}"
            )

    async def send(self, message: Dict[str, Any]) -> None:
        """
        Send a message to the Kafka topic

        Args:
            message: The message to send

        Raises:
            RuntimeError: If the producer is not started
            Exception: If sending the message fails
        """
        if not self._started or not self._producer:
            raise RuntimeError(f"Kafka producer for topic '{self.topic}' not started")

        try:
            await self._producer.send_and_wait(self.topic, message)
            logger.debug(f"Sent message to Kafka topic '{self.topic}'")
        except Exception as e:
            logger.error(f"Failed to send Kafka message to topic '{self.topic}': {e}")
            raise
