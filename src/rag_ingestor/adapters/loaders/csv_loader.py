from typing import List
from langchain_community.document_loaders import CSVLoader as LangchainCSVLoader
from langchain_core.documents import Document

from rag_ingestor.adapters.loaders.base import BaseDocumentLoader


class CSVLoader(BaseDocumentLoader):
    def load(self, path: str) -> List[Document]:
        return LangchainCSVLoader(path).load()
