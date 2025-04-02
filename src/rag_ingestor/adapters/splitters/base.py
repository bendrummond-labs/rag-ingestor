# src/rag_ingestor/adapters/splitters/base.py
from abc import ABC, abstractmethod
from typing import Iterable, List
from langchain_core.documents import Document


class TextSplitter(ABC):
    """Base interface for text splitters"""

    @abstractmethod
    def split_documents(self, documents: Iterable[Document]) -> List[Document]:
        """
        Split documents into chunks

        Args:
            documents: Documents to split

        Returns:
            List of split document chunks
        """
        pass
