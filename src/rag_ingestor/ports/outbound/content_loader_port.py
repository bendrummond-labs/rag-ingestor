from abc import ABC
from pathlib import Path
from typing import List

from rag_ingestor.domain.model import Content


class ContentLoaderPort(ABC):
    def load_content(self, source: Path, **kwargs) -> List[Content]:
        """Load content from a source."""
        pass
