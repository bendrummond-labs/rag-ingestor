"""
Langchain document loader adapter for the RAG ingestor.

This module provides an adapter that implements the ContentLoaderPort interface
using Langchain's document loaders. It serves as a bridge between the domain
layer and the Langchain library, allowing the application to load various
document types through a consistent interface.
"""

from pathlib import Path
from typing import List, Dict, Optional, Type, Any
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    UnstructuredHTMLLoader,
    CSVLoader,
)
from langchain.document_loaders.base import BaseLoader

from rag_ingestor.ports.outbound.content_loader_port import ContentLoaderPort
from rag_ingestor.domain.model import Content


class LangchainDocumentLoaderAdapter(ContentLoaderPort):
    """
    Adapter that implements ContentLoaderPort using Langchain document loaders.

    This adapter maps file extensions to appropriate Langchain document loaders
    and converts Langchain Document objects to domain Content entities.

    Attributes:
        loaders: Dictionary mapping file extensions to Langchain loader classes
    """

    # Default mapping of file extensions to Langchain loader classes
    LOADER_MAPPING = {
        ".txt": TextLoader,
        ".pdf": PyPDFLoader,
        ".html": UnstructuredHTMLLoader,
        ".htm": UnstructuredHTMLLoader,
        ".csv": CSVLoader,
    }

    def __init__(self, custom_loaders: Optional[Dict[str, Type[BaseLoader]]] = None):
        """
        Initialize the adapter with default and custom loaders.

        Args:
            custom_loaders: Optional dictionary mapping file extensions to
                            custom Langchain loader classes
        """
        # Start with default loaders
        self.loaders = {**self.LOADER_MAPPING}

        # Add any custom loaders provided
        if custom_loaders:
            self.loaders.update(custom_loaders)

    def load_content(self, source: Path, **kwargs) -> List[Content]:
        """
        Load content from a source file using appropriate Langchain loader.

        This method implements the ContentLoaderPort interface by selecting
        the appropriate Langchain loader based on the file extension and
        converting the loaded documents to domain Content entities.

        Args:
            source: Path object pointing to the file to load
            **kwargs: Additional keyword arguments to pass to the loader

        Returns:
            List of Content domain entities

        Raises:
            ValueError: If the source is not a Path or has an unsupported extension
        """
        # Validate input is a Path object
        if not isinstance(source, Path):
            raise ValueError("Source must be a Path object.")

        # Get file extension and validate it's supported
        file_ext = source.suffix.lower()
        if file_ext not in self.loaders:
            raise ValueError(
                f"Unsupported file type: {file_ext}. Supported types are: {list(self.loaders.keys())}"
            )

        # Get the appropriate loader class and instantiate it
        loader_class = self.loaders[file_ext]
        loader = loader_class(str(source), **kwargs)

        # Load documents using Langchain
        documents = loader.load()
        contents: List[Content] = []

        # Convert each Langchain Document to a domain Content entity
        for doc in documents:
            # Merge source path with document metadata
            metadata = self._prepare_metadata(source, doc.metadata)

            # Create Content entity
            content = Content(text=doc.page_content, metadata=metadata)
            contents.append(content)

        return contents

    def _prepare_metadata(
        self, source: Path, doc_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Prepare metadata for Content creation by merging source information
        with document metadata.

        Args:
            source: Path object of the source file
            doc_metadata: Metadata from Langchain document

        Returns:
            Dictionary of merged metadata
        """
        # Create a copy to avoid modifying the original
        metadata = {"source": str(source)}

        # Add document metadata
        if doc_metadata:
            metadata.update(doc_metadata)

        return metadata
