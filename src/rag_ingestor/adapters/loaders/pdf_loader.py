from typing import List
from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain_core.documents import Document

from rag_ingestor.adapters.loaders.base import BaseDocumentLoader


class PDFLoader(BaseDocumentLoader):
    def load(self, path: str) -> List[Document]:
        return UnstructuredPDFLoader(path).load()
