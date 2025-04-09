from pathlib import Path
from typing import List, Dict, Optional, Type
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

    LOADER_MAPPING = {
        ".txt": TextLoader,
        ".pdf": PyPDFLoader,
        ".html": UnstructuredHTMLLoader,
        ".htm": UnstructuredHTMLLoader,
        ".csv": CSVLoader,
    }

    def __init__(self, custom_loaders: Optional[Dict[str, Type[BaseLoader]]] = None):
        self.loaders = {**self.LOADER_MAPPING}
        if custom_loaders:
            self.loaders.update(custom_loaders)

    def load_content(self, source: Path, **kwargs) -> List[Content]:

        if not isinstance(source, Path):
            raise ValueError("Source must be a Path object.")

        file_ext = source.suffix.lower()

        if file_ext not in self.loaders:
            raise ValueError(
                f"Unsupported file type: {file_ext}. Supported types are: {list(self.loaders.keys())}"
            )

        loader_class = self.loaders[file_ext]
        loader = loader_class(str(source), **kwargs)

        documents = loader.load()
        contents = []

        for doc in documents:
            metadata = {"source": source, **doc.metadata}

            content = Content(text=doc.page_content, metadata=metadata)
            contents.append(content)

        return contents
