from typing import Iterable, List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from rag_ingestor.adapters.splitters.base import TextSplitter


class PlainTextSplitter(TextSplitter):
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def split_documents(self, documents: Iterable[Document]) -> List[Document]:
        return self.splitter.split_documents(documents)
