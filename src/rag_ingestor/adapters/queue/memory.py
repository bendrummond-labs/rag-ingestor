import logging
import datetime
from typing import Any, Dict, List

from rag_ingestor.adapters.queue.base import MessageQueue

logger = logging.getLogger(__name__)


class InMemoryMessageQueue(MessageQueue):
    """In-memory implementation of the MessageQueue interface, useful for testing"""

    def __init__(self):
        self.queues: Dict[str, List[Dict[str, Any]]] = {}
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize the in-memory message queue"""
        self.initialized = True
        logger.info("In-memory message queue initialized")

    async def shutdown(self) -> None:
        """Clear all queues"""
        self.queues.clear()
        self.initialized = False
        logger.info("In-memory message queue shutdown")

    async def send_message(self, queue_name: str, message: Dict[str, Any]) -> bool:
        """
        Store a message in an in-memory queue

        Args:
            queue_name: Name of the queue
            message: Message payload

        Returns:
            bool: Always True unless not initialized
        """
        if not self.initialized:
            logger.error("In-memory message queue not initialized")
            return False

        if queue_name not in self.queues:
            self.queues[queue_name] = []

        # Add timestamp if not present
        if "timestamp" not in message:
            message["timestamp"] = datetime.datetime.now().isoformat()

        self.queues[queue_name].append(message)
        logger.info(f"Stored message in queue '{queue_name}'")
        return True

    def get_messages(self, queue_name: str) -> List[Dict[str, Any]]:
        """
        Get all messages from a queue

        Args:
            queue_name: Name of the queue

        Returns:
            List of messages in the queue
        """
        return self.queues.get(queue_name, [])
