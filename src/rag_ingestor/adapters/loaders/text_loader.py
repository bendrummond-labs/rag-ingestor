from typing import List
from langchain_community.document_loaders import TextLoader as LangchainTextLoader
from langchain_core.documents import Document

from rag_ingestor.adapters.loaders.base import BaseDocumentLoader


class TextLoader(BaseDocumentLoader):
    def load(self, path: str) -> List[Document]:
        return LangchainTextLoader(path, encoding="utf-8").load()
