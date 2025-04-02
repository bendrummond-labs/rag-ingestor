from pathlib import Path
from typing import Dict, List, Optional
import logging
from langchain_core.documents import Document

from rag_ingestor.adapters.loaders.base import BaseDocumentLoader


logger = logging.getLogger(__name__)


class LoaderManager:
    """Manager for document loaders"""

    def __init__(self):
        self.loaders: Dict[str, BaseDocumentLoader] = {}

    def register_loader(self, extension: str, loader: BaseDocumentLoader) -> None:
        """Register a loader for a file extension"""
        self.loaders[extension.lower()] = loader
        logger.debug(f"Registered loader for extension: {extension}")

    def get_loader(self, extension: str) -> Optional[BaseDocumentLoader]:
        """Get a loader for a file extension"""
        return self.loaders.get(extension.lower())

    def load_document(self, path: str) -> List[Document]:
        """Load a document using the appropriate loader"""
        ext = Path(path).suffix.lower()

        loader = self.get_loader(ext)
        if not loader:
            supported = ", ".join(self.loaders.keys())
            raise ValueError(f"Unsupported file type '{ext}'. Supported: {supported}")

        return loader.load(path)
