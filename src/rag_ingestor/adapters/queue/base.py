from abc import ABC, abstractmethod
from typing import Any, Dict


class MessageQueue(ABC):

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the message queue connection.
        """
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the message queue connection"""
        pass

    @abstractmethod
    async def send_message(self, queue_name: str, message: Dict[str, Any]) -> bool:
        """
        Send a message to the specified queue

        Args:
            queue_name: Name of the queue/topic
            message: Message payload to send

        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        pass
