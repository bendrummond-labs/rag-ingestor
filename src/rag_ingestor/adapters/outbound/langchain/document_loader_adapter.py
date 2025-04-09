from pathlib import Path
from typing import List, Dict, Optional, Type, Union
from langchain.document_loaders import (
    TextLoader,
    PyPDFLoader,
    UnstructuredHTMLLoader,
    CSVLoader,
)

from langchain.document_loaders.base import BaseLoader

from rag_ingestor.ports.outbound.content_loader_port import ContentLoaderPort
from src.rag_ingestor.domain.model import Content


class LangchainDocumentLoaderAdapter(ContentLoaderPort):

    LOADER_MAPPING = {
        ".txt": TextLoader,
        ".pdf": PyPDFLoader,
        ".html": UnstructuredHTMLLoader,
        ".htm": UnstructuredHTMLLoader,
        ".csv": CSVLoader,
    }

    def __init__(self, custom_loaders: Optional[Dict[str, Type[BaseLoader]]] = None):
        self.loader = {**self.LOADER_MAPPING}
        if custom_loaders:
            self.loaders.update(custom_loaders)

    def load_content(self, source: Union[Path, str], **kwargs) -> List[Content]:

        source_path = Path(source) if isinstance(source, str) else source

        file_ext = source_path.suffix.lower()

        if file_ext not in self.loader:
            raise ValueError(
                f"Unsupported file type: {file_ext}. Supported types are: {list(self.loader.keys())}"
            )

        loader_class = self.loader[file_ext]
        loader = loader_class(str(source_path), **kwargs)

        documents = loader.load()
        contents = []

        for doc in documents:
            metadata = {"source": source_path, **doc.metadata}

            content = Content(text=doc.page_content, metadata=metadata)
            contents.append(content)

        return contents
