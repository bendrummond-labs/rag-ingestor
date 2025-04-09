from pathlib import Path
from typing import List, Dict, Optional, Type, Union
from langchain_community.document_loaders import (
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
        self.loaders = {**self.LOADER_MAPPING}
        if custom_loaders:
            self.loaders.update(custom_loaders)

    def load_content(
        self, source: Union[Path, str], type: str, **kwargs
    ) -> List[Content]:

        source_path = Path(source) if isinstance(source, str) else source
        print(f"Loading content from: {source_path}")

        if type not in self.loaders:
            raise ValueError(
                f"Unsupported file type: {type}. Supported types are: {list(self.loaders.keys())}"
            )

        loader_class = self.loaders[type]
        loader = loader_class(str(source_path), **kwargs)

        documents = loader.load()
        contents = []

        for doc in documents:
            metadata = {"source": source_path, **doc.metadata}

            content = Content(text=doc.page_content, metadata=metadata)
            contents.append(content)

        return contents
