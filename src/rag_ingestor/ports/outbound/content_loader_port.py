from abc import ABC
from pathlib import Path
from typing import Union

from src.rag_ingestor.domain.model import Content


class ContentLoaderPort(ABC):
    def load_content(self, source: Union[str, Path], **kwargs) -> Content:
        """Load content from a source."""
        pass
