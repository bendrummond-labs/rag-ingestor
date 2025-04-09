from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from rag_ingestor.domain.model import Content, ContentChunk


class TextChunkingPort(ABC):

    @abstractmethod
    def chunk_content(
        self, content: Content, chunk_params: Optional[Dict[str, Any]] = None
    ) -> List[ContentChunk]:
        pass
