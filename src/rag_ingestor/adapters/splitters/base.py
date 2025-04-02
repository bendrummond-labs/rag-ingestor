from abc import ABC, abstractmethod
from typing import Iterable, List, Type, Dict
from langchain_core.documents import Document


class BaseSplitterService(ABC):
    @abstractmethod
    def split_documents(self, documents: Iterable[Document]) -> List[Document]:
        pass


SPLITTER_SERVICE_REGISTRY: Dict[str, Type[BaseSplitterService]] = {}


def register_splitter(splitter_type: str):
    def decorator(cls: Type[BaseSplitterService]):
        SPLITTER_SERVICE_REGISTRY[splitter_type] = cls
        return cls

    return decorator
