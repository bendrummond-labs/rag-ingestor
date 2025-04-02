from typing import Literal
from rag_ingestor.adapters.queue.base import MessageQueue


#########HATE THIS PATTERN#########
def get_message_queue(queue_type: Literal["kafka", "memory"] = "kafka") -> MessageQueue:

    if queue_type == "kafka":
        from rag_ingestor.adapters.queue.kafka import KafkaMessageQueue

        return KafkaMessageQueue.get_instance()
    elif queue_type == "memory":
        from rag_ingestor.adapters.queue.memory import InMemoryMessageQueue

        return InMemoryMessageQueue()
    else:
        raise ValueError(f"Unsupported message queue type: {queue_type}")
