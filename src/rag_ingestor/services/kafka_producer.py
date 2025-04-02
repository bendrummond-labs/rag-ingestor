import logging
from typing import Any, Dict

from aiokafka import AIOKafkaProducer
from orjson import dumps

from rag_ingestor.config import settings

logger = logging.getLogger(__name__)


class KafkaProducerService:
    def __init__(self, topic: str):
        self.topic = topic
        self._producer: AIOKafkaProducer | None = None

    async def start(self):
        self._producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BROKER_URL,
            value_serializer=lambda v: dumps(v),
        )
        await self._producer.start()
        logger.info("Kafka producer started")

    async def stop(self):
        if self._producer:
            await self._producer.stop()
            logger.info("Kafka producer stopped")

    async def send(self, message: Dict[str, Any]):
        if not self._producer:
            raise RuntimeError("Kafka producer not started")

        try:
            await self._producer.send_and_wait(self.topic, message)
            logger.debug(f"Sent message to Kafka topic '{self.topic}'")
        except Exception as e:
            logger.error(f"Failed to send Kafka message: {e}")
            raise
