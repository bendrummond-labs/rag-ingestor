import logging
import json
from typing import Any, Dict
from aiokafka import AIOKafkaProducer

from rag_ingestor.config import settings

logger = logging.getLogger(__name__)


class KafkaProducerService:
    def __init__(self, topic: str):
        self.topic = topic
        self._producer: AIOKafkaProducer | None = None

    async def start(self):
        try:
            self._producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BROKER_URL,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
            await self._producer.start()
            logger.info(
                f"Kafka producer started, connected to {settings.KAFKA_BROKER_URL}"
            )
        except Exception as e:
            logger.error(f"Failed to start Kafka producer: {str(e)}")
            raise

    async def stop(self):
        if self._producer:
            try:
                await self._producer.stop()
                logger.info("Kafka producer stopped")
            except Exception as e:
                logger.error(f"Error stopping Kafka producer: {str(e)}")

    async def send(self, message: Dict[str, Any]):
        if not self._producer:
            raise RuntimeError("Kafka producer not started")

        try:
            await self._producer.send_and_wait(self.topic, message)
            logger.debug(f"Sent message to Kafka topic '{self.topic}'")
        except Exception as e:
            logger.error(f"Failed to send Kafka message: {e}")
            raise
