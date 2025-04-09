from abc import ABC
from pathlib import Path
from typing import List, Union

from src.rag_ingestor.domain.model import Content


class ContentLoaderPort(ABC):
    def load_content(
        self, source: Union[str, Path], type: str, **kwargs
    ) -> List[Content]:
        """Load content from a source."""
        pass
