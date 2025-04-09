from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

from rag_ingestor.domain.model import ContentChunk


class MessageQueuePort(ABC):
    @abstractmethod
    async def publish_chunks(
        self, chunks: List[ContentChunk], metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def publish_event(
        self, event_type: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def close(self) -> None:
        pass
