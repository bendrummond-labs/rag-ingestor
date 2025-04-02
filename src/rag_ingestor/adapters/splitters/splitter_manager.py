from typing import Dict, Type
import logging

from rag_ingestor.adapters.splitters.base import TextSplitter
from rag_ingestor.adapters.splitters.plain_splitter import PlainTextSplitter
from rag_ingestor.adapters.splitters.markdown_splitter import MarkdownSplitter


logger = logging.getLogger(__name__)


class SplitterManager:
    """Manager for text splitters"""

    def __init__(self):
        self.splitter_types: Dict[str, Type[TextSplitter]] = {}

    def register_splitter(self, name: str, splitter_cls: Type[TextSplitter]) -> None:
        """Register a splitter type"""
        self.splitter_types[name] = splitter_cls
        logger.debug(f"Registered splitter type: {name}")

    def get_splitter(
        self, splitter_type: str, chunk_size: int = 500, chunk_overlap: int = 100
    ) -> TextSplitter:
        """
        Get a splitter instance by type

        Args:
            splitter_type: Type of splitter to use
            chunk_size: Size of each chunk
            chunk_overlap: Overlap between chunks

        Returns:
            TextSplitter instance

        Raises:
            ValueError: If splitter type is not registered
        """
        splitter_cls = self.splitter_types.get(splitter_type)

        if not splitter_cls:
            supported = ", ".join(self.splitter_types.keys())
            raise ValueError(
                f"Unsupported splitter type: {splitter_type}. Supported: {supported}"
            )

        return splitter_cls(chunk_size=chunk_size, chunk_overlap=chunk_overlap)


def create_default_splitter_manager() -> SplitterManager:
    """Create and configure a splitter manager with all supported splitters"""
    manager = SplitterManager()

    # Register all supported splitters
    manager.register_splitter("plain", PlainTextSplitter)
    manager.register_splitter("markdown", MarkdownSplitter)

    return manager
