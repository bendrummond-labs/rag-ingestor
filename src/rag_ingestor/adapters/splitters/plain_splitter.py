from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter

from rag_ingestor.adapters.splitters.base import BaseSplitterService, register_splitter


@register_splitter("plain")
class PlainTextSplitterService(BaseSplitterService):
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def split_text(self, text: str) -> List[str]:
        return self.splitter.split_text(text)
