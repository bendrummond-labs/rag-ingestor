from pathlib import Path
import logging
from typing import Callable, Dict, List
from langchain.docstore.document import Document
from importlib import import_module


logger = logging.getLogger(__name__)


_LOADER_REGISTRY: Dict[str, Callable[[str], List[Document]]] = {}


def register_loader(extension: str):
    def wrapper(fn: Callable[[str], List[Document]]):
        _LOADER_REGISTRY[extension.lower()] = fn
        return fn

    return wrapper


def load_file(path: str) -> List[Document]:
    ext = Path(path).suffix.lower()
    if ext not in _LOADER_REGISTRY:
        supported = ", ".join(_LOADER_REGISTRY.keys())
        raise ValueError(f"Unsupported file type '{ext}'. Supported: {supported}")
    return _LOADER_REGISTRY[ext](path)


def _load_all_loaders():
    for module in ["text_loader", "pdf_loader", "csv_loader"]:
        import_module(f"rag_ingestor.ingestion.loaders.{module}")


_load_all_loaders()
