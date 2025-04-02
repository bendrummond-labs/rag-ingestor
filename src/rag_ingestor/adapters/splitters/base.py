from abc import ABC, abstractmethod
from typing import List, Type, Dict


class BaseSplitterService(ABC):
    @abstractmethod
    def split_text(self, text: str) -> List[str]:
        pass


SPLITTER_SERVICE_REGISTRY: Dict[str, Type[BaseSplitterService]] = {}


def register_splitter(splitter_type: str):
    def decorator(cls: Type[BaseSplitterService]):
        SPLITTER_SERVICE_REGISTRY[splitter_type] = cls
        return cls

    return decorator
