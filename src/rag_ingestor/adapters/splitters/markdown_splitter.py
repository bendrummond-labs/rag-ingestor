from typing import Iterable, List
from langchain_text_splitters import MarkdownTextSplitter
from langchain_core.documents import Document

from rag_ingestor.adapters.splitters.base import TextSplitter


class MarkdownSplitter(TextSplitter):
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100):
        self.splitter = MarkdownTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )

    def split_documents(self, documents: Iterable[Document]) -> List[Document]:
        return self.splitter.split_documents(documents)
