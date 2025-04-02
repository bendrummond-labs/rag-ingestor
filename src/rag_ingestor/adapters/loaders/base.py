from abc import ABC, abstractmethod
from typing import List
from langchain_core.documents import Document


class BaseDocumentLoader(ABC):
    @abstractmethod
    def load(self, path: str) -> List[Document]:
        """
        Load a document from a file path

        Args:
            path: Path to the document

        Returns:
            List of document objects
        """
        pass
