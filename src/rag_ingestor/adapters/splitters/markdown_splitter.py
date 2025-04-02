from typing import List
from langchain_text_splitters import MarkdownTextSplitter
from rag_ingestor.adapters.splitters.base import BaseSplitterService, register_splitter


@register_splitter("markdown")
class MarkdownSplitterService(BaseSplitterService):
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100):
        self.splitter = MarkdownTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )

    def split_text(self, text: str) -> List[str]:
        return self.splitter.split_text(text)
